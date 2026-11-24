from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Iterable

import joblib
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon
from sklearn.decomposition import PCA as SklearnPCA
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
)
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from data.nap import doc_va_kiem_ke
from data.tien_xu_ly import (
    TEN_COT_MAC_DINH,
    ap_chuan_hoa,
    chia_phan_tang,
    khop_chuan_hoa,
    lay_mau_con,
    ma_hoa_nhan,
    tiem_ngoai_lai,
)
from experiments.cau_hinh import (
    COT_NGOAI_LAI,
    HAT_GIONG as SEED_MAC_DINH,
    HE_SO_NGOAI_LAI,
    LUOI_D_TNA,
    LUOI_D_TNB,
    LUOI_KC_TNB,
    N_INIT_KMEANS,
    N_MAU_DAY_DU,
    N_MAU_NHANH,
    NGUONG_CAT_SVD_MAHAL,
    SEEDS_DAY_DU,
    SEEDS_NHANH,
    TIKHONOV_LAMBDA,
    TY_LE_KIEM_TRA,
    TY_LE_NGOAI_LAI,
)
from models.khoang_cach import (
    do_bo_nho,
    gan_gan_nhat,
    ma_tran_khoang_cach,
    silhouette_nhieu_phan_hoach,
    silhouette_theo_khoi,
)
from models.kmeans import kmeans
from models.mahalanobis import (
    can_chinh_nhan_hungarian,
    do_so_dieu_kien_pca,
    ma_tran_mahalanobis,
    phan_ra_mahalanobis,
    so_sanh_ba_phan_hoach,
)
from models.pam import gan_medoid, pam
from models.pca import chieu, khop_pca

THU_MUC_BANG = ROOT_DIR / "results" / "bang"
THU_MUC_MO_HINH = ROOT_DIR / "results" / "mo_hinh"
THU_MUC_CHECKPOINT = THU_MUC_BANG / "checkpoints"


def _comb2(x: np.ndarray | float) -> np.ndarray | float:
    return x * (x - 1.0) * 0.5


def bang_cheo(
    y: np.ndarray | pd.Series,
    nhan: np.ndarray | pd.Series,
    ten_lop: list[str] | None = None,
) -> pd.DataFrame:
    """Lập bảng chéo lớp thật (hàng) × cụm tìm được (cột)."""
    y_arr = np.asarray(y)
    nhan_arr = np.asarray(nhan)
    if len(y_arr) != len(nhan_arr):
        raise ValueError("y và nhan phải có cùng độ dài.")

    if ten_lop is None:
        lop_list = sorted(np.unique(y_arr).tolist(), key=str)
    else:
        lop_list = list(ten_lop)

    cum_list = sorted(np.unique(nhan_arr).tolist())
    lop_map = {v: i for i, v in enumerate(lop_list)}
    cum_map = {v: j for j, v in enumerate(cum_list)}

    mat = np.zeros((len(lop_list), len(cum_list)), dtype=np.int64)
    y_idx = np.fromiter((lop_map[v] for v in y_arr), dtype=np.int64, count=len(y_arr))
    c_idx = np.fromiter((cum_map[v] for v in nhan_arr), dtype=np.int64, count=len(nhan_arr))
    np.add.at(mat, (y_idx, c_idx), 1)

    cols = [f"Cum_{c}" for c in cum_list]
    return pd.DataFrame(mat, index=[str(l) for l in lop_list], columns=cols)


def ari(y: np.ndarray | pd.Series, nhan: np.ndarray | pd.Series) -> float:
    """Chỉ số Adjusted Rand Index (Hubert & Arabie) tự viết bằng NumPy."""
    y_arr = np.asarray(y)
    nhan_arr = np.asarray(nhan)
    n = len(y_arr)
    if n != len(nhan_arr):
        raise ValueError("y và nhan phải có cùng độ dài.")
    if n < 2:
        return 1.0

    _, y_inv = np.unique(y_arr, return_inverse=True)
    _, c_inv = np.unique(nhan_arr, return_inverse=True)
    n_lop = int(y_inv.max()) + 1
    n_cum = int(c_inv.max()) + 1

    if n_lop == 1 and n_cum == 1:
        return 1.0
    if n_lop == 1 or n_cum == 1:
        return 0.0

    bang = np.zeros((n_lop, n_cum), dtype=np.float64)
    np.add.at(bang, (y_inv, c_inv), 1.0)

    tong_hang = bang.sum(axis=1)
    tong_cot = bang.sum(axis=0)

    sum_comb_nij = float(np.sum(_comb2(bang)))
    sum_comb_ai = float(np.sum(_comb2(tong_hang)))
    sum_comb_bj = float(np.sum(_comb2(tong_cot)))
    total_comb = float(_comb2(float(n)))

    expected = (sum_comb_ai * sum_comb_bj) / total_comb
    max_idx = 0.5 * (sum_comb_ai + sum_comb_bj)
    denom = max_idx - expected
    if denom == 0.0:
        return 1.0 if np.isclose(sum_comb_nij, expected) else 0.0
    return float((sum_comb_nij - expected) / denom)


def nmi(y: np.ndarray | pd.Series, nhan: np.ndarray | pd.Series) -> float:
    """Chỉ số Normalized Mutual Information (trung bình cộng) tự viết bằng NumPy."""
    y_arr = np.asarray(y)
    nhan_arr = np.asarray(nhan)
    n = len(y_arr)
    if n != len(nhan_arr):
        raise ValueError("y và nhan phải có cùng độ dài.")
    if n == 0:
        return 1.0

    _, y_inv = np.unique(y_arr, return_inverse=True)
    _, c_inv = np.unique(nhan_arr, return_inverse=True)
    n_lop = int(y_inv.max()) + 1
    n_cum = int(c_inv.max()) + 1

    if n_lop == 1 and n_cum == 1:
        return 1.0
    if n_lop == 1 or n_cum == 1:
        return 0.0

    bang = np.zeros((n_lop, n_cum), dtype=np.float64)
    np.add.at(bang, (y_inv, c_inv), 1.0)

    p_ij = bang / float(n)
    p_i = p_ij.sum(axis=1)
    p_j = p_ij.sum(axis=0)

    h_u = float(-np.sum(p_i[p_i > 0.0] * np.log(p_i[p_i > 0.0])))
    h_v = float(-np.sum(p_j[p_j > 0.0] * np.log(p_j[p_j > 0.0])))
    if h_u + h_v == 0.0:
        return 1.0

    nz_r, nz_c = np.nonzero(p_ij > 0.0)
    mi = float(np.sum(p_ij[nz_r, nz_c] * np.log(p_ij[nz_r, nz_c] / (p_i[nz_r] * p_j[nz_c]))))
    # Khử sai số âm cực nhỏ gần 0
    mi = max(0.0, mi)
    return float(2.0 * mi / (h_u + h_v))


def _chuan_bi_khong_gian(
    X_tr: np.ndarray,
    y_tr: np.ndarray,
    n_mau: int,
    seed: int,
    co_ngoai_lai: bool,
    chuan_hoa: bool = True,
) -> dict[str, Any]:
    """Chuẩn bị mẫu con, tiêm ngoại lai (nếu có), chuẩn hóa và PCA cho một seed."""
    idx_mau = lay_mau_con(y_tr, n_mau=n_mau, seed=seed)
    if co_ngoai_lai:
        X_dung, info_out = tiem_ngoai_lai(
            X_tr,
            ty_le=TY_LE_NGOAI_LAI,
            he_so=HE_SO_NGOAI_LAI,
            cot=COT_NGOAI_LAI,
            seed=seed,
        )
    else:
        X_dung = X_tr
        info_out = None

    if chuan_hoa:
        scaler = khop_chuan_hoa(X_dung)
        Z_tr = ap_chuan_hoa(scaler, X_dung)
        pca_mh = khop_pca(Z_tr)
    else:
        scaler = None
        Z_tr = np.asarray(X_dung, dtype=np.float64)
        pca_mh = None

    return {
        "X_tr": np.asarray(X_dung, dtype=np.float64),
        "Z_tr": Z_tr,
        "y_tr": y_tr,
        "idx_mau": idx_mau,
        "scaler": scaler,
        "pca": pca_mh,
        "info_ngoai_lai": info_out,
        "seed": int(seed),
        "co_ngoai_lai": bool(co_ngoai_lai),
    }


def _lay_ma_tran_d_chieu(du_lieu: dict[str, Any], d: int) -> np.ndarray:
    """Lấy ma trận đặc trưng d chiều: d=16 dùng Z_tr (hoặc X_tr thô), d<16 dùng PCA."""
    Z_tr = du_lieu["Z_tr"]
    if d == Z_tr.shape[1]:
        return Z_tr
    if du_lieu["pca"] is None:
        raise ValueError("Không thể chiếu PCA khi dữ liệu chưa chuẩn hóa.")
    return chieu(du_lieu["pca"], Z_tr, d)


def chay_mot(
    du_lieu: dict[str, Any],
    d: int,
    kc: int,
    seed: int,
    thuat_toan: str,
    co_ngoai_lai: bool = False,
    D_sub: np.ndarray | None = None,
    t_dist: float = 0.0,
    tinh_sil: bool = True,
) -> dict[str, Any]:
    """Chạy một cấu hình đơn lẻ (gom trên mẫu con nếu PAM/k-means, gán toàn bộ tập train)."""
    y_tr = du_lieu["y_tr"]
    idx_mau = du_lieu["idx_mau"]

    if thuat_toan == "mot_cum":
        t0 = time.perf_counter()
        nhan_all = np.zeros(len(y_tr), dtype=np.int64)
        tg = time.perf_counter() - t0
        return {
            "dieu_kien": "ngoai_lai" if co_ngoai_lai else "sach",
            "thuat_toan": "mot_cum",
            "d": int(d),
            "kc": 1,
            "seed": int(seed),
            "ari": ari(y_tr, nhan_all),
            "nmi": nmi(y_tr, nhan_all),
            "sil": 0.0,
            "sil_goc16": 0.0,
            "thoi_gian": float(tg),
            "thoi_gian_s": float(tg),
            "chi_phi": np.nan,
            "medoid_toan_cuc": [],
            "nhan_toan_bo": nhan_all,
        }

    if thuat_toan == "kmeans_chua_chuan_hoa":
        space = du_lieu["X_tr"]
        d_eff = space.shape[1]
    else:
        space = _lay_ma_tran_d_chieu(du_lieu, d)
        d_eff = int(d)

    X_sub = space[idx_mau]

    if thuat_toan == "pam":
        t0 = time.perf_counter()
        if D_sub is None:
            D_local = ma_tran_khoang_cach(X_sub, co_khoi=1024)
            t_local_dist = time.perf_counter() - t0
        else:
            D_local = D_sub
            t_local_dist = float(t_dist)
        t_algo_start = time.perf_counter()
        res = pam(D_local, k=kc)
        medoid_global = idx_mau[res["medoid"]].astype(np.int64)
        nhan_all = gan_medoid(space, space[medoid_global])
        tg = t_local_dist + (time.perf_counter() - t_algo_start)
        chi_phi_val = float(res["chi_phi"])
        med_list = medoid_global.tolist()
    elif thuat_toan in ("kmeans", "kmeans_chua_chuan_hoa"):
        t0 = time.perf_counter()
        res = kmeans(X_sub, k=kc, n_init=N_INIT_KMEANS, seed=seed)
        nhan_all, _ = gan_gan_nhat(space, res["tam"])
        tg = time.perf_counter() - t0
        chi_phi_val = float(res["sse"])
        med_list = []
    else:
        raise ValueError(f"Thuật toán không hợp lệ: {thuat_toan}")

    sil_val = silhouette_theo_khoi(space, nhan_all, co_khoi=1024)[1] if tinh_sil else np.nan
    sil_goc16 = (
        sil_val
        if (d_eff == 16 or not tinh_sil or thuat_toan == "kmeans_chua_chuan_hoa")
        else silhouette_theo_khoi(du_lieu["Z_tr"], nhan_all, co_khoi=1024)[1]
    )

    return {
        "dieu_kien": "ngoai_lai" if co_ngoai_lai else "sach",
        "thuat_toan": thuat_toan,
        "d": int(d_eff),
        "kc": int(kc),
        "seed": int(seed),
        "ari": ari(y_tr, nhan_all),
        "nmi": nmi(y_tr, nhan_all),
        "sil": float(sil_val),
        "sil_goc16": float(sil_goc16),
        "thoi_gian": float(tg),
        "thoi_gian_s": float(tg),
        "chi_phi": chi_phi_val,
        "medoid_toan_cuc": med_list,
        "nhan_toan_bo": nhan_all,
    }


def _chay_mot_seed_dieu_kien(
    X_tr: np.ndarray,
    y_tr: np.ndarray,
    dk_sorted: list[tuple[int, int]],
    n_mau: int,
    seed: int,
    co_out: bool,
    chay_baseline: bool,
    ckpt_file: Path | None,
    limit_blas: bool = False,
) -> list[dict[str, Any]]:
    """Chạy trọn một cặp (dieu_kien, seed) và lưu checkpoint CSV nếu có."""
    if limit_blas:
        os.environ.setdefault("OMP_NUM_THREADS", "1")
        os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
        os.environ.setdefault("MKL_NUM_THREADS", "1")

    nhan_dk = "ngoai_lai" if co_out else "sach"
    if ckpt_file is not None and ckpt_file.exists():
        df_ckpt = pd.read_csv(ckpt_file)
        print(f"  [Checkpoint] Đọc lại {ckpt_file.name} ({len(df_ckpt)} dòng)", flush=True)
        return df_ckpt.to_dict(orient="records")

    t_seed0 = time.perf_counter()
    du_lieu = _chuan_bi_khong_gian(
        X_tr, y_tr, n_mau=n_mau, seed=seed, co_ngoai_lai=co_out, chuan_hoa=True
    )
    hang_seed: list[dict[str, Any]] = []

    # Gom các mức k theo từng chiều d để tái dùng D_sub và tính silhouette 1 lượt/chiều
    theo_d: dict[int, list[int]] = {}
    for d, kc in dk_sorted:
        theo_d.setdefault(d, []).append(kc)

    can_tinh_sil_goc16: list[tuple[int, np.ndarray]] = []

    for d in sorted(theo_d.keys()):
        space = _lay_ma_tran_d_chieu(du_lieu, d)
        t_d0 = time.perf_counter()
        D_sub = ma_tran_khoang_cach(space[du_lieu["idx_mau"]], co_khoi=1024)
        t_dist = time.perf_counter() - t_d0

        hang_d: list[dict[str, Any]] = []
        ds_nhan_d: list[np.ndarray] = []

        for kc in theo_d[d]:
            for algo in ("pam", "kmeans"):
                kq = chay_mot(
                    du_lieu,
                    d=d,
                    kc=kc,
                    seed=seed,
                    thuat_toan=algo,
                    co_ngoai_lai=co_out,
                    D_sub=D_sub if algo == "pam" else None,
                    t_dist=t_dist if algo == "pam" else 0.0,
                    tinh_sil=False,
                )
                nhan_all = kq.pop("nhan_toan_bo")
                kq.pop("medoid_toan_cuc")
                kq.pop("thoi_gian", None)
                hang_d.append(kq)
                ds_nhan_d.append(nhan_all)

        ds_sil_d = silhouette_nhieu_phan_hoach(space, ds_nhan_d, co_khoi=1024)
        for kq, sil_val, nhan_all in zip(hang_d, ds_sil_d, ds_nhan_d):
            kq["sil"] = float(sil_val)
            if d == 16:
                kq["sil_goc16"] = float(sil_val)
            elif kq["kc"] == 7:
                can_tinh_sil_goc16.append((len(hang_seed), nhan_all))
            hang_seed.append(kq)

    if can_tinh_sil_goc16:
        ds_sil16 = silhouette_nhieu_phan_hoach(
            du_lieu["Z_tr"], [nh for _, nh in can_tinh_sil_goc16], co_khoi=1024
        )
        for (row_idx, _), s16 in zip(can_tinh_sil_goc16, ds_sil16):
            hang_seed[row_idx]["sil_goc16"] = float(s16)

    if chay_baseline:
        kq_1c = chay_mot(
            du_lieu, d=16, kc=1, seed=seed, thuat_toan="mot_cum", co_ngoai_lai=co_out
        )
        hang_seed.append(
            {
                k_col: v
                for k_col, v in kq_1c.items()
                if k_col not in ("medoid_toan_cuc", "nhan_toan_bo", "thoi_gian")
            }
        )

        kq_raw = chay_mot(
            du_lieu,
            d=16,
            kc=7,
            seed=seed,
            thuat_toan="kmeans_chua_chuan_hoa",
            co_ngoai_lai=co_out,
        )
        hang_seed.append(
            {
                k_col: v
                for k_col, v in kq_raw.items()
                if k_col not in ("medoid_toan_cuc", "nhan_toan_bo", "thoi_gian")
            }
        )

    if ckpt_file is not None:
        pd.DataFrame(hang_seed).to_csv(ckpt_file, index=False, encoding="utf-8-sig")

    print(
        f"  [Quét] {nhan_dk:9s} | seed={seed} | {len(hang_seed)} dòng | {time.perf_counter() - t_seed0:.1f}s",
        flush=True,
    )
    return hang_seed


def quet(
    X_tr: np.ndarray,
    y_tr: np.ndarray,
    luoi_d: Iterable[int] = LUOI_D_TNB,
    luoi_kc: Iterable[int] = LUOI_KC_TNB,
    seeds: Iterable[int] = SEEDS_DAY_DU,
    ngoai_lai: bool | Iterable[bool] = (False, True),
    n_mau: int = N_MAU_DAY_DU,
    cap_dk_bo_sung: Iterable[tuple[int, int]] | None = None,
    chay_baseline: bool = True,
    thu_muc_checkpoint: Path | None = None,
    workers: int = 1,
) -> pd.DataFrame:
    """Quét lưới (d, k) × seeds × điều kiện sạch/ngoại lai và xuất DataFrame dạng dài."""
    dk_set = {(int(d), int(k)) for d in luoi_d for k in luoi_kc}
    if cap_dk_bo_sung is not None:
        dk_set.update((int(d), int(k)) for d, k in cap_dk_bo_sung)
    dk_sorted = sorted(dk_set)

    if isinstance(ngoai_lai, bool):
        dk_ngoai_lai = [ngoai_lai]
    else:
        dk_ngoai_lai = [bool(v) for v in ngoai_lai]

    seeds_list = [int(s) for s in seeds]
    if thu_muc_checkpoint is not None:
        thu_muc_checkpoint.mkdir(parents=True, exist_ok=True)

    nhiem_vu: list[tuple[bool, int, Path | None]] = []
    for co_out in dk_ngoai_lai:
        nhan_dk = "ngoai_lai" if co_out else "sach"
        for seed in seeds_list:
            ckpt_file = (
                thu_muc_checkpoint / f"ckpt_{nhan_dk}_seed_{seed}.csv"
                if thu_muc_checkpoint is not None
                else None
            )
            nhiem_vu.append((co_out, seed, ckpt_file))

    tat_ca_hang: list[dict[str, Any]] = []
    if workers <= 1 or len(nhiem_vu) <= 1:
        for co_out, seed, ckpt_file in nhiem_vu:
            tat_ca_hang.extend(
                _chay_mot_seed_dieu_kien(
                    X_tr, y_tr, dk_sorted, n_mau, seed, co_out, chay_baseline, ckpt_file, False
                )
            )
    else:
        with ProcessPoolExecutor(max_workers=int(workers)) as pool:
            futs = [
                pool.submit(
                    _chay_mot_seed_dieu_kien,
                    X_tr,
                    y_tr,
                    dk_sorted,
                    n_mau,
                    seed,
                    co_out,
                    chay_baseline,
                    ckpt_file,
                    True,
                )
                for co_out, seed, ckpt_file in nhiem_vu
            ]
            for fut in as_completed(futs):
                tat_ca_hang.extend(fut.result())

    cot_chuan = [
        "dieu_kien",
        "thuat_toan",
        "d",
        "kc",
        "seed",
        "ari",
        "nmi",
        "sil",
        "sil_goc16",
        "thoi_gian_s",
        "chi_phi",
    ]
    df_out = pd.DataFrame(tat_ca_hang)[cot_chuan]
    return df_out.sort_values(["dieu_kien", "seed", "d", "kc", "thuat_toan"]).reset_index(drop=True)


def _fmt_mean_std(mean: float, std: float, digits: int = 3) -> str:
    return f"{mean:.{digits}f}±{std:.{digits}f}"


def tong_hop(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Tổng hợp Mean ± SD cho điều kiện sạch, ngoại lai và bảng ghép trước–sau."""
    nhom = (
        df.groupby(["dieu_kien", "thuat_toan", "d", "kc"], as_index=False)
        .agg(
            ari_mean=("ari", "mean"),
            ari_std=("ari", lambda s: float(np.std(s, ddof=1)) if len(s) > 1 else 0.0),
            nmi_mean=("nmi", "mean"),
            nmi_std=("nmi", lambda s: float(np.std(s, ddof=1)) if len(s) > 1 else 0.0),
            sil_mean=("sil", "mean"),
            sil_std=("sil", lambda s: float(np.std(s, ddof=1)) if len(s) > 1 else 0.0),
            sil_goc16_mean=("sil_goc16", "mean"),
            sil_goc16_std=("sil_goc16", lambda s: float(np.std(s, ddof=1)) if len(s) > 1 else 0.0),
            time_mean=("thoi_gian_s", "mean"),
            time_std=("thoi_gian_s", lambda s: float(np.std(s, ddof=1)) if len(s) > 1 else 0.0),
            so_seed=("seed", "nunique"),
        )
    )

    bang_sach = nhom[nhom["dieu_kien"] == "sach"].copy().reset_index(drop=True)
    bang_ngoai_lai = nhom[nhom["dieu_kien"] == "ngoai_lai"].copy().reset_index(drop=True)

    # Bảng trước–sau ghép theo (thuat_toan, d, kc, seed) để tính đúng ΔARI từng cặp seed
    df_sach = df[df["dieu_kien"] == "sach"][["thuat_toan", "d", "kc", "seed", "ari", "nmi", "sil", "thoi_gian_s"]]
    df_out = df[df["dieu_kien"] == "ngoai_lai"][["thuat_toan", "d", "kc", "seed", "ari", "nmi", "sil", "thoi_gian_s"]]
    ghep = df_sach.merge(df_out, on=["thuat_toan", "d", "kc", "seed"], suffixes=("_sach", "_ngoai_lai"))
    ghep["delta_ari"] = ghep["ari_ngoai_lai"] - ghep["ari_sach"]
    ghep["delta_nmi"] = ghep["nmi_ngoai_lai"] - ghep["nmi_sach"]

    bang_truoc_sau = (
        ghep.groupby(["thuat_toan", "d", "kc"], as_index=False)
        .agg(
            ari_sach_mean=("ari_sach", "mean"),
            ari_sach_std=("ari_sach", lambda s: float(np.std(s, ddof=1)) if len(s) > 1 else 0.0),
            ari_ngoai_lai_mean=("ari_ngoai_lai", "mean"),
            ari_ngoai_lai_std=("ari_ngoai_lai", lambda s: float(np.std(s, ddof=1)) if len(s) > 1 else 0.0),
            delta_ari_mean=("delta_ari", "mean"),
            delta_ari_std=("delta_ari", lambda s: float(np.std(s, ddof=1)) if len(s) > 1 else 0.0),
            nmi_sach_mean=("nmi_sach", "mean"),
            nmi_ngoai_lai_mean=("nmi_ngoai_lai", "mean"),
            delta_nmi_mean=("delta_nmi", "mean"),
            sil_sach_mean=("sil_sach", "mean"),
            sil_sach_std=("sil_sach", lambda s: float(np.std(s, ddof=1)) if len(s) > 1 else 0.0),
            sil_ngoai_lai_mean=("sil_ngoai_lai", "mean"),
            sil_ngoai_lai_std=("sil_ngoai_lai", lambda s: float(np.std(s, ddof=1)) if len(s) > 1 else 0.0),
            time_sach_mean=("thoi_gian_s_sach", "mean"),
            time_sach_std=("thoi_gian_s_sach", lambda s: float(np.std(s, ddof=1)) if len(s) > 1 else 0.0),
            time_ngoai_lai_mean=("thoi_gian_s_ngoai_lai", "mean"),
            time_ngoai_lai_std=("thoi_gian_s_ngoai_lai", lambda s: float(np.std(s, ddof=1)) if len(s) > 1 else 0.0),
        )
    )

    return bang_sach, bang_ngoai_lai, bang_truoc_sau


def xuat_benchmark_table(bang_truoc_sau: pd.DataFrame) -> dict[str, list[dict[str, Any]]]:
    """Định dạng bảng trước–sau thành schema JSON mà dry_bean_web sử dụng (khóa '2', '4', '16')."""
    ket_qua: dict[str, list[dict[str, Any]]] = {}

    for d_val in LUOI_D_TNB:
        sub = bang_truoc_sau[bang_truoc_sau["d"] == d_val]
        pam_sub = sub[sub["thuat_toan"] == "pam"].set_index("kc")
        km_sub = sub[sub["thuat_toan"] == "kmeans"].set_index("kc")
        ks_chung = sorted(set(pam_sub.index).intersection(km_sub.index))

        rows: list[dict[str, Any]] = []
        for k_val in ks_chung:
            rp = pam_sub.loc[k_val]
            rk = km_sub.loc[k_val]
            rows.append(
                {
                    "k": int(k_val),
                    "cMed": _fmt_mean_std(rp["ari_sach_mean"], rp["ari_sach_std"], 3),
                    "cKm": _fmt_mean_std(rk["ari_sach_mean"], rk["ari_sach_std"], 3),
                    "cSil": _fmt_mean_std(rp["sil_sach_mean"], rp["sil_sach_std"], 3),
                    "cSilKm": _fmt_mean_std(rk["sil_sach_mean"], rk["sil_sach_std"], 3),
                    "cTime": _fmt_mean_std(rp["time_sach_mean"], rp["time_sach_std"], 2),
                    "oMed": _fmt_mean_std(rp["ari_ngoai_lai_mean"], rp["ari_ngoai_lai_std"], 3),
                    "oKm": _fmt_mean_std(rk["ari_ngoai_lai_mean"], rk["ari_ngoai_lai_std"], 3),
                    "oSil": _fmt_mean_std(rp["sil_ngoai_lai_mean"], rp["sil_ngoai_lai_std"], 3),
                    "oSilKm": _fmt_mean_std(rk["sil_ngoai_lai_mean"], rk["sil_ngoai_lai_std"], 3),
                    "oTime": _fmt_mean_std(rp["time_ngoai_lai_mean"], rp["time_ngoai_lai_std"], 2),
                    "dMed": round(float(rp["delta_ari_mean"]), 4),
                    "dKm": round(float(rk["delta_ari_mean"]), 4),
                }
            )
        ket_qua[str(d_val)] = rows

    return ket_qua


def _wilcoxon_an_toan(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    diff = np.asarray(x, dtype=np.float64) - np.asarray(y, dtype=np.float64)
    if len(diff) == 0 or np.allclose(diff, 0.0, atol=1e-15):
        return 0.0, 1.0
    stat, p_val = wilcoxon(x, y, zero_method="wilcox", alternative="two-sided")
    return float(stat), float(p_val)


def kiem_dinh_wilcoxon(
    df: pd.DataFrame,
    cac_d: Iterable[int] = (2, 4, 16),
    kc: int = 7,
) -> pd.DataFrame:
    """Thực hiện kiểm định Wilcoxon ghép cặp theo seed giữa PAM và k-means."""
    ket_qua: list[dict[str, Any]] = []

    for d_val in cac_d:
        for dieu_kien in ("sach", "ngoai_lai"):
            sub = df[(df["d"] == d_val) & (df["kc"] == kc) & (df["dieu_kien"] == dieu_kien)]
            pam_s = sub[sub["thuat_toan"] == "pam"].sort_values("seed")
            km_s = sub[sub["thuat_toan"] == "kmeans"].sort_values("seed")
            ghep = pam_s.merge(km_s, on="seed", suffixes=("_pam", "_km"))
            if len(ghep) == 0:
                continue
            stat, p_val = _wilcoxon_an_toan(ghep["ari_pam"].to_numpy(), ghep["ari_km"].to_numpy())
            chenh = ghep["ari_pam"] - ghep["ari_km"]
            ket_qua.append(
                {
                    "phep_so": f"ARI_{dieu_kien}_PAM_vs_KMeans",
                    "d": int(d_val),
                    "kc": int(kc),
                    "so_cap_seed": int(len(ghep)),
                    "trung_binh_pam": float(ghep["ari_pam"].mean()),
                    "trung_binh_kmeans": float(ghep["ari_km"].mean()),
                    "chenh_lech_tb": float(chenh.mean()),
                    "wilcoxon_stat": stat,
                    "p_value": p_val,
                    "co_y_nghia_005": bool(p_val < 0.05),
                }
            )

        # Kiểm định mức tụt ΔARI = ARI_ngoại_lai - ARI_sạch giữa PAM và k-means
        sach = df[(df["d"] == d_val) & (df["kc"] == kc) & (df["dieu_kien"] == "sach")]
        out = df[(df["d"] == d_val) & (df["kc"] == kc) & (df["dieu_kien"] == "ngoai_lai")]
        delta_pam = (
            sach[sach["thuat_toan"] == "pam"][["seed", "ari"]]
            .merge(out[out["thuat_toan"] == "pam"][["seed", "ari"]], on="seed", suffixes=("_s", "_o"))
        )
        delta_km = (
            sach[sach["thuat_toan"] == "kmeans"][["seed", "ari"]]
            .merge(out[out["thuat_toan"] == "kmeans"][["seed", "ari"]], on="seed", suffixes=("_s", "_o"))
        )
        delta_ghep = delta_pam.merge(delta_km, on="seed", suffixes=("_pam", "_km"))
        if len(delta_ghep) > 0:
            dp = (delta_ghep["ari_o_pam"] - delta_ghep["ari_s_pam"]).to_numpy()
            dk = (delta_ghep["ari_o_km"] - delta_ghep["ari_s_km"]).to_numpy()
            stat, p_val = _wilcoxon_an_toan(dp, dk)
            ket_qua.append(
                {
                    "phep_so": "DeltaARI_PAM_vs_KMeans",
                    "d": int(d_val),
                    "kc": int(kc),
                    "so_cap_seed": int(len(delta_ghep)),
                    "trung_binh_pam": float(dp.mean()),
                    "trung_binh_kmeans": float(dk.mean()),
                    "chenh_lech_tb": float((dp - dk).mean()),
                    "wilcoxon_stat": stat,
                    "p_value": p_val,
                    "co_y_nghia_005": bool(p_val < 0.05),
                }
            )

    return pd.DataFrame(ket_qua)


def phan_lop_moc_tren(
    X: np.ndarray,
    y: np.ndarray,
    seed: int = SEED_MAC_DINH,
) -> tuple[pd.DataFrame, pd.DataFrame, Pipeline]:
    """Chạy phân lớp RandomForest làm mốc trên (80/20 phân tầng + CV 5-fold chống rò rỉ)."""
    X_tr, X_te, y_tr, y_te, _, _ = chia_phan_tang(X, y, ty_le_test=0.2, seed=seed)
    ten_lop = sorted(np.unique(y).tolist())

    cau_hinh: list[tuple[str, int | None, str]] = [
        ("Dummy_LopPhoBienNhat", None, "dummy"),
        ("RF_16D_StandardScaler", None, "rf"),
        ("RF_PCA_d4_StandardScaler", 4, "rf"),
        ("RF_PCA_d2_StandardScaler", 2, "rf"),
        ("RF_PCA_d7_StandardScaler", 7, "rf"),
    ]

    dong_kq: list[dict[str, Any]] = []
    mo_hinh_chinh: Pipeline | None = None
    cm_df = pd.DataFrame()

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=int(seed))

    for ten_ch, n_comp, loai in cau_hinh:
        steps: list[tuple[str, Any]] = [("scaler", StandardScaler())]
        if n_comp is not None:
            steps.append(("pca", SklearnPCA(n_components=n_comp, random_state=int(seed))))
        if loai == "dummy":
            steps.append(("clf", DummyClassifier(strategy="most_frequent")))
        else:
            steps.append(
                ("rf", RandomForestClassifier(n_estimators=200, random_state=int(seed), n_jobs=-1))
            )
        pipe = Pipeline(steps)

        cv_res = cross_validate(
            pipe,
            X_tr,
            y_tr,
            cv=cv,
            scoring=["accuracy", "f1_macro", "f1_weighted"],
            n_jobs=-1,
        )

        pipe.fit(X_tr, y_tr)
        y_pred = pipe.predict(X_te)

        dong_kq.append(
            {
                "cau_hinh": ten_ch,
                "so_chieu": 16 if n_comp is None else int(n_comp),
                "test_accuracy": float(accuracy_score(y_te, y_pred)),
                "test_f1_macro": float(f1_score(y_te, y_pred, average="macro")),
                "test_f1_weighted": float(f1_score(y_te, y_pred, average="weighted")),
                "test_ari": ari(y_te, y_pred),
                "test_nmi": nmi(y_te, y_pred),
                "cv5_accuracy_mean": float(np.mean(cv_res["test_accuracy"])),
                "cv5_accuracy_std": float(np.std(cv_res["test_accuracy"], ddof=1)),
                "cv5_f1_macro_mean": float(np.mean(cv_res["test_f1_macro"])),
                "cv5_f1_macro_std": float(np.std(cv_res["test_f1_macro"], ddof=1)),
            }
        )

        if ten_ch == "RF_16D_StandardScaler":
            mo_hinh_chinh = pipe
            cm = confusion_matrix(y_te, y_pred, labels=ten_lop)
            cm_df = pd.DataFrame(cm, index=ten_lop, columns=[f"Du_doan_{l}" for l in ten_lop])

    assert mo_hinh_chinh is not None
    return pd.DataFrame(dong_kq), cm_df, mo_hinh_chinh


def khao_sat_nhom_dac_trung(
    X_tr: np.ndarray,
    y_tr: np.ndarray,
    seeds: Iterable[int],
    n_mau: int,
) -> pd.DataFrame:
    """Khảo sát thêm (mức Xuất sắc): 12 cột đọc thẳng vs 4 hệ số ShapeFactor vs cả 16 cột."""
    nhom_cot = {
        "12_cot_doc_thang": list(range(0, 12)),
        "4_he_so_dan_xuat": list(range(12, 16)),
        "ca_16_cot": list(range(0, 16)),
    }
    hang: list[dict[str, Any]] = []

    for seed in seeds:
        idx_mau = lay_mau_con(y_tr, n_mau=n_mau, seed=int(seed))
        X_out, _ = tiem_ngoai_lai(
            X_tr, ty_le=TY_LE_NGOAI_LAI, he_so=HE_SO_NGOAI_LAI, cot=COT_NGOAI_LAI, seed=int(seed)
        )
        for dieu_kien, X_nguon in (("sach", X_tr), ("ngoai_lai", X_out)):
            for ten_nhom, cols in nhom_cot.items():
                X_sub_cols = X_nguon[:, cols]
                scaler = khop_chuan_hoa(X_sub_cols)
                Z = ap_chuan_hoa(scaler, X_sub_cols)
                D_sub = ma_tran_khoang_cach(Z[idx_mau], co_khoi=1024)

                res_pam = pam(D_sub, k=7)
                med_g = idx_mau[res_pam["medoid"]]
                nhan_pam = gan_medoid(Z, Z[med_g])
                sil_pam = silhouette_theo_khoi(Z, nhan_pam, co_khoi=1024)[1]

                res_km = kmeans(Z[idx_mau], k=7, n_init=N_INIT_KMEANS, seed=int(seed))
                nhan_km, _ = gan_gan_nhat(Z, res_km["tam"])
                sil_km = silhouette_theo_khoi(Z, nhan_km, co_khoi=1024)[1]

                hang.append(
                    {
                        "nhom_dac_trung": ten_nhom,
                        "so_cot": len(cols),
                        "dieu_kien": dieu_kien,
                        "seed": int(seed),
                        "ari_pam": ari(y_tr, nhan_pam),
                        "nmi_pam": nmi(y_tr, nhan_pam),
                        "sil_pam": sil_pam,
                        "ari_kmeans": ari(y_tr, nhan_km),
                        "nmi_kmeans": nmi(y_tr, nhan_km),
                        "sil_kmeans": sil_km,
                    }
                )

    df_raw = pd.DataFrame(hang)
    df_sum = (
        df_raw.groupby(["nhom_dac_trung", "so_cot", "dieu_kien"], as_index=False)
        .agg(
            ari_pam_mean=("ari_pam", "mean"),
            ari_pam_std=("ari_pam", lambda s: float(np.std(s, ddof=1)) if len(s) > 1 else 0.0),
            ari_kmeans_mean=("ari_kmeans", "mean"),
            ari_kmeans_std=("ari_kmeans", lambda s: float(np.std(s, ddof=1)) if len(s) > 1 else 0.0),
            sil_pam_mean=("sil_pam", "mean"),
            sil_kmeans_mean=("sil_kmeans", "mean"),
        )
    )
    return df_sum


def chay_mo_rong_mahalanobis(
    X_tr: np.ndarray,
    y_tr: np.ndarray,
    seeds: Iterable[int],
    n_mau: int,
    thu_muc_luu: Path = THU_MUC_BANG,
) -> dict[str, pd.DataFrame]:
    """Hướng mở rộng A: So sánh Euclid chuẩn hóa, Euclid sau PCA (d=4) và Mahalanobis (SVD/Tikhonov)."""
    scaler = khop_chuan_hoa(X_tr)
    Z_tr = ap_chuan_hoa(scaler, X_tr)
    pca_mh = khop_pca(Z_tr)
    P_4 = chieu(pca_mh, Z_tr, 4)

    mahal_pinv = phan_ra_mahalanobis(Z_tr, nguong_cat=NGUONG_CAT_SVD_MAHAL, tikonov=0.0)
    Z_w_pinv = Z_tr @ mahal_pinv["W"].T

    mahal_tik = phan_ra_mahalanobis(Z_tr, nguong_cat=0.0, tikonov=TIKHONOV_LAMBDA)
    Z_w_tik = Z_tr @ mahal_tik["W"].T

    df_cond = do_so_dieu_kien_pca(Z_tr)
    df_cond.to_csv(thu_muc_luu / "mo_rong_mahalanobis_so_dieu_kien.csv", index=False, encoding="utf-8-sig")

    khong_gian = {
        "Euclid_16D_ChuanHoa": Z_tr,
        "Euclid_PCA_d4": P_4,
        "Mahalanobis_SVD_pinv": Z_w_pinv,
        "Mahalanobis_Tikhonov": Z_w_tik,
    }

    hang: list[dict[str, Any]] = []
    nhan_seed0: dict[str, np.ndarray] = {}

    for i_s, seed in enumerate(seeds):
        idx_mau = lay_mau_con(y_tr, n_mau=n_mau, seed=int(seed))
        for ten_loi, sp in khong_gian.items():
            t0 = time.perf_counter()
            if ten_loi.startswith("Mahalanobis"):
                W_use = mahal_pinv["W"] if ten_loi == "Mahalanobis_SVD_pinv" else mahal_tik["W"]
                D_sub = ma_tran_mahalanobis(Z_tr[idx_mau], W_use, co_khoi=1024)
            else:
                D_sub = ma_tran_khoang_cach(sp[idx_mau], co_khoi=1024)
            res = pam(D_sub, k=7)
            med_g = idx_mau[res["medoid"]]
            nhan_all = gan_medoid(sp, sp[med_g])
            tg = time.perf_counter() - t0
            sil_val = silhouette_theo_khoi(sp, nhan_all, co_khoi=1024)[1]

            hang.append(
                {
                    "phuong_phap": ten_loi,
                    "seed": int(seed),
                    "ari": ari(y_tr, nhan_all),
                    "nmi": nmi(y_tr, nhan_all),
                    "sil": float(sil_val),
                    "thoi_gian_s": float(tg),
                }
            )
            if i_s == 0 and ten_loi != "Mahalanobis_Tikhonov":
                nhan_seed0[ten_loi] = nhan_all

    df_raw = pd.DataFrame(hang)
    df_bang = (
        df_raw.groupby("phuong_phap", as_index=False)
        .agg(
            ari_mean=("ari", "mean"),
            ari_std=("ari", lambda s: float(np.std(s, ddof=1)) if len(s) > 1 else 0.0),
            nmi_mean=("nmi", "mean"),
            nmi_std=("nmi", lambda s: float(np.std(s, ddof=1)) if len(s) > 1 else 0.0),
            sil_mean=("sil", "mean"),
            sil_std=("sil", lambda s: float(np.std(s, ddof=1)) if len(s) > 1 else 0.0),
            time_mean=("thoi_gian_s", "mean"),
        )
    )
    df_bang.to_csv(thu_muc_luu / "mo_rong_mahalanobis_bang3loi.csv", index=False, encoding="utf-8-sig")

    df_ari_3x3, df_pct_3x3 = so_sanh_ba_phan_hoach(nhan_seed0, ari)
    df_ari_3x3.to_csv(thu_muc_luu / "mo_rong_mahalanobis_trung_lap_ari.csv", encoding="utf-8-sig")
    df_pct_3x3.to_csv(thu_muc_luu / "mo_rong_mahalanobis_trung_lap_pct.csv", encoding="utf-8-sig")

    # Canh nhãn 3 phân hoạch về cùng chuẩn tham chiếu Euclid_16D_ChuanHoa để liệt kê các hạt xếp khác nhau
    n_euc = nhan_seed0["Euclid_16D_ChuanHoa"]
    n_pca = can_chinh_nhan_hungarian(n_euc, nhan_seed0["Euclid_PCA_d4"])
    n_mah = can_chinh_nhan_hungarian(n_euc, nhan_seed0["Mahalanobis_SVD_pinv"])

    khac_mask = (n_euc != n_pca) | (n_euc != n_mah) | (n_pca != n_mah)
    idx_khac = np.where(khac_mask)[0]
    df_khac = pd.DataFrame(X_tr[idx_khac], columns=list(TEN_COT_MAC_DINH))
    df_khac.insert(0, "idx_train", idx_khac)
    df_khac.insert(1, "Class", y_tr[idx_khac])
    df_khac["cum_Euclid16"] = n_euc[idx_khac]
    df_khac["cum_PCA_d4"] = n_pca[idx_khac]
    df_khac["cum_Mahalanobis"] = n_mah[idx_khac]
    df_khac.to_csv(thu_muc_luu / "mo_rong_mahalanobis_hat_khac_nhau.csv", index=False, encoding="utf-8-sig")

    return {
        "bang3loi": df_bang,
        "trung_lap_ari": df_ari_3x3,
        "trung_lap_pct": df_pct_3x3,
        "hat_khac_nhau": df_khac,
        "so_dieu_kien": df_cond,
    }


def luu_mo_hinh(
    X_tr: np.ndarray,
    y_tr: np.ndarray,
    rf_model: Pipeline,
    thu_muc: Path = THU_MUC_MO_HINH,
) -> None:
    """Huấn luyện và lưu bộ chuẩn hóa, PCA, medoid PAM, tâm k-means và RandomForest."""
    thu_muc.mkdir(parents=True, exist_ok=True)

    scaler = khop_chuan_hoa(X_tr)
    Z_tr = ap_chuan_hoa(scaler, X_tr)
    pca_mh = khop_pca(Z_tr)
    P_4 = chieu(pca_mh, Z_tr, 4)

    idx_mau = lay_mau_con(y_tr, n_mau=min(N_MAU_DAY_DU, len(y_tr)), seed=SEED_MAC_DINH)
    D_4 = ma_tran_khoang_cach(P_4[idx_mau], co_khoi=1024)
    res_pam_4 = pam(D_4, k=7)
    res_km_4 = kmeans(P_4[idx_mau], k=7, n_init=N_INIT_KMEANS, seed=SEED_MAC_DINH)

    D_16 = ma_tran_khoang_cach(Z_tr[idx_mau], co_khoi=1024)
    res_pam_16 = pam(D_16, k=7)
    res_km_16 = kmeans(Z_tr[idx_mau], k=7, n_init=N_INIT_KMEANS, seed=SEED_MAC_DINH)

    joblib.dump(scaler, thu_muc / "scaler.joblib")
    joblib.dump(pca_mh, thu_muc / "pca_svd.joblib")
    joblib.dump(
        {
            "d4": {
                "medoid_idx_train": idx_mau[res_pam_4["medoid"]],
                "medoid_toa_do": P_4[idx_mau[res_pam_4["medoid"]]],
                "chi_phi": res_pam_4["chi_phi"],
                "lich_su_chi_phi": res_pam_4["lich_su_chi_phi"],
            },
            "d16": {
                "medoid_idx_train": idx_mau[res_pam_16["medoid"]],
                "medoid_toa_do": Z_tr[idx_mau[res_pam_16["medoid"]]],
                "chi_phi": res_pam_16["chi_phi"],
                "lich_su_chi_phi": res_pam_16["lich_su_chi_phi"],
            },
        },
        thu_muc / "pam_k7.joblib",
    )
    joblib.dump(
        {
            "d4": {"tam": res_km_4["tam"], "sse": res_km_4["sse"]},
            "d16": {"tam": res_km_16["tam"], "sse": res_km_16["sse"]},
        },
        thu_muc / "kmeans_k7.joblib",
    )
    joblib.dump(rf_model, thu_muc / "rf_moc_tren.joblib")


def main(nhanh: bool = False, workers: int = 1) -> dict[str, Any]:
    """Chạy toàn bộ thực nghiệm Bước 4–7 và xuất bảng kết quả vào results/bang/."""
    THU_MUC_BANG.mkdir(parents=True, exist_ok=True)
    THU_MUC_MO_HINH.mkdir(parents=True, exist_ok=True)

    arff_path = ROOT_DIR / "data" / "raw" / "DryBeanDataset" / "Dry_Bean_Dataset.arff"
    _, X_df, y_s = doc_va_kiem_ke(arff_path)
    X_all = X_df.to_numpy(dtype=np.float64)
    y_all = y_s.to_numpy(dtype=str)
    _, ten_lop = ma_hoa_nhan(y_all)

    # 1. Đo bộ nhớ ma trận n×n (Bước 4)
    cac_n_mem = (500, 1000, 2000, 3000) if nhanh else (1000, 2000, 3000, 5000)
    df_mem = do_bo_nho(cac_n=cac_n_mem, duong_dan_luu=THU_MUC_BANG / "bo_nho_ma_tran.csv")
    print(f"[OK] Đã đo bộ nhớ ma trận -> {THU_MUC_BANG / 'bo_nho_ma_tran.csv'}")

    # 2. Chia phân tầng 80/20 một lần (Bước 3)
    X_tr, X_te, y_tr, y_te, _, _ = chia_phan_tang(
        X_all, y_all, ty_le_test=TY_LE_KIEM_TRA, seed=SEED_MAC_DINH
    )
    seeds = SEEDS_NHANH if nhanh else SEEDS_DAY_DU
    n_mau = N_MAU_NHANH if nhanh else N_MAU_DAY_DU

    # 3. Lưu thông tin tiêm ngoại lai từng seed để kiểm chứng công bằng
    tiem_log = {}
    for s in seeds:
        _, info = tiem_ngoai_lai(
            X_tr, ty_le=TY_LE_NGOAI_LAI, he_so=HE_SO_NGOAI_LAI, cot=COT_NGOAI_LAI, seed=s
        )
        tiem_log[str(s)] = {
            "seed": int(s),
            "cot": info["cot"],
            "so_hat_tiem": int(len(info["idx"])),
            "idx": info["idx"].tolist(),
            "he_so": [round(float(v), 6) for v in info["he_so"]],
        }
    with open(THU_MUC_BANG / "tiem_ngoai_lai_seed.json", "w", encoding="utf-8") as f:
        json.dump(tiem_log, f, ensure_ascii=False, indent=2)

    # 4. Quét TN-A (d=2..16 tại k=7) và TN-B (d∈{2,4,16} × k=2..16)
    cap_tna = [(d, 7) for d in LUOI_D_TNA]
    ckpt_dir = (THU_MUC_CHECKPOINT / ("nhanh" if nhanh else "day_du"))
    print(
        f"\n--- BẮT ĐẦU QUÉT THỰC NGHIỆM ({'NHANH' if nhanh else 'ĐẦY ĐỦ'}: n_mau={n_mau}, {len(seeds)} seeds, workers={workers}) ---",
        flush=True,
    )
    df_tho = quet(
        X_tr,
        y_tr,
        luoi_d=LUOI_D_TNB,
        luoi_kc=LUOI_KC_TNB,
        seeds=seeds,
        ngoai_lai=(False, True),
        n_mau=n_mau,
        cap_dk_bo_sung=cap_tna,
        chay_baseline=True,
        thu_muc_checkpoint=ckpt_dir,
        workers=workers,
    )
    df_tho.to_csv(THU_MUC_BANG / "ket_qua_tho.csv", index=False, encoding="utf-8-sig")

    # 5. Tổng hợp bảng chính, bảng phụ, bảng trước–sau & benchmark JSON cho web
    bang_sach, bang_ngoai_lai, bang_truoc_sau = tong_hop(df_tho)
    bang_sach.to_csv(THU_MUC_BANG / "bang_chinh_sach.csv", index=False, encoding="utf-8-sig")
    bang_ngoai_lai.to_csv(THU_MUC_BANG / "bang_phu_ngoai_lai.csv", index=False, encoding="utf-8-sig")
    bang_truoc_sau.to_csv(THU_MUC_BANG / "bang_truoc_sau.csv", index=False, encoding="utf-8-sig")

    benchmark_json = xuat_benchmark_table(bang_truoc_sau)
    for ten_json in ("benchmarkTable.json", "benchmark_results.json"):
        with open(THU_MUC_BANG / ten_json, "w", encoding="utf-8") as f:
            json.dump(benchmark_json, f, ensure_ascii=False, indent=2)

    # 6. Kiểm định Wilcoxon ghép cặp
    df_wilcoxon = kiem_dinh_wilcoxon(df_tho, cac_d=LUOI_D_TNB, kc=7)
    df_wilcoxon.to_csv(THU_MUC_BANG / "kiem_dinh_wilcoxon.csv", index=False, encoding="utf-8-sig")

    # 7. Bảng chéo cụm × giống tại k=7 và k_sil (chọn k không nhìn nhãn) ở d=4 (giữ >=94-95% phương sai)
    pam_d4_sach = bang_sach[(bang_sach["thuat_toan"] == "pam") & (bang_sach["d"] == 4)]
    k_sil = int(pam_d4_sach.loc[pam_d4_sach["sil_mean"].idxmax(), "kc"])

    du_lieu_sach_0 = _chuan_bi_khong_gian(
        X_tr, y_tr, n_mau=n_mau, seed=seeds[0], co_ngoai_lai=False, chuan_hoa=True
    )
    kq_k7 = chay_mot(du_lieu_sach_0, d=4, kc=7, seed=seeds[0], thuat_toan="pam", tinh_sil=False)
    bc_k7 = bang_cheo(y_tr, kq_k7["nhan_toan_bo"], ten_lop=ten_lop)
    bc_k7.to_csv(THU_MUC_BANG / "bang_cheo_k7.csv", encoding="utf-8-sig")

    kq_ksil = chay_mot(du_lieu_sach_0, d=4, kc=k_sil, seed=seeds[0], thuat_toan="pam", tinh_sil=False)
    bc_ksil = bang_cheo(y_tr, kq_ksil["nhan_toan_bo"], ten_lop=ten_lop)
    bc_ksil.to_csv(THU_MUC_BANG / "bang_cheo_k_sil.csv", encoding="utf-8-sig")

    # 8. Khảo sát nhóm 12 cột đọc thẳng vs 4 hệ số ShapeFactor (mức Xuất sắc)
    df_nhom_cot = khao_sat_nhom_dac_trung(X_tr, y_tr, seeds=seeds, n_mau=n_mau)
    df_nhom_cot.to_csv(THU_MUC_BANG / "khao_sat_nhom_dac_trung.csv", index=False, encoding="utf-8-sig")

    # 9. Hướng mở rộng A: Mahalanobis qua SVD vs Euclid chuẩn hóa vs Euclid sau PCA
    mo_rong_mahal = chay_mo_rong_mahalanobis(X_tr, y_tr, seeds=seeds, n_mau=n_mau)

    # 10. Phân lớp mốc trên RandomForest (+ Dummy lớp phổ biến nhất) & lưu mô hình
    df_rf, cm_rf, rf_model = phan_lop_moc_tren(X_all, y_all, seed=SEED_MAC_DINH)
    df_rf.to_csv(THU_MUC_BANG / "phan_lop_moc_tren.csv", index=False, encoding="utf-8-sig")
    cm_rf.to_csv(THU_MUC_BANG / "ma_tran_nham_lan_rf.csv", encoding="utf-8-sig")

    luu_mo_hinh(X_tr, y_tr, rf_model, thu_muc=THU_MUC_MO_HINH)

    print("\n[HOÀN TẤT BƯỚC 4–7] Đã lưu toàn bộ bảng tại results/bang/ và mô hình tại results/mo_hinh/.")
    return {
        "df_tho": df_tho,
        "bang_sach": bang_sach,
        "bang_ngoai_lai": bang_ngoai_lai,
        "bang_truoc_sau": bang_truoc_sau,
        "df_wilcoxon": df_wilcoxon,
        "df_rf": df_rf,
        "df_mem": df_mem,
        "mo_rong_mahalanobis": mo_rong_mahal,
        "k_sil": k_sil,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chạy thực nghiệm DA14 Dry Bean (Bước 4–7).")
    parser.add_argument(
        "--nhanh",
        action="store_true",
        help="Chế độ smoke test nhanh (n_mau=600, 2 seeds) để kiểm tra pipeline.",
    )
    parser.add_argument(
        "--tat-ca",
        action="store_true",
        help="Chạy toàn bộ thí nghiệm đầy đủ (mặc định khi không truyền --nhanh).",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Số tiến trình song song theo từng (điều kiện, seed). Mặc định 1.",
    )
    args = parser.parse_args()
    main(nhanh=args.nhanh and not args.tat_ca, workers=args.workers)

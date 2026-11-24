from __future__ import annotations

import gc
import os
from pathlib import Path
from typing import Iterator, Sequence

import numpy as np
import pandas as pd
import psutil

ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_MEMORY_CSV = ROOT_DIR / "results" / "bang" / "bo_nho_ma_tran.csv"


def euclid_theo_khoi(
    A: np.ndarray,
    B: np.ndarray | None = None,
    co_khoi: int = 1024,
    binh_phuong: bool = False,
    kiem_tra_gan: bool = True,
) -> Iterator[tuple[int, int, np.ndarray]]:
    """Sinh từng khối ma trận khoảng cách Euclid giữa A và B theo kích thước co_khoi."""
    if co_khoi <= 0:
        raise ValueError("co_khoi phải lớn hơn 0.")

    A_arr = np.asarray(A, dtype=np.float64)
    tu_doi_xung = B is None
    B_arr = A_arr if tu_doi_xung else np.asarray(B, dtype=np.float64)

    # Trừ trung bình chung trước để giảm triệt tiêu số học khi dữ liệu có thang đo lớn
    mu = B_arr.mean(axis=0)
    Ac = A_arr - mu
    Bc = B_arr - mu

    a2 = np.sum(Ac * Ac, axis=1)
    b2 = np.sum(Bc * Bc, axis=1)
    Bc_T = Bc.T
    scale_max = float(max(a2.max(initial=0.0), b2.max(initial=0.0), 1.0))

    n_a = len(A_arr)
    for i0 in range(0, n_a, co_khoi):
        i1 = min(i0 + co_khoi, n_a)
        d2 = a2[i0:i1, None] + b2[None, :] - 2.0 * (Ac[i0:i1] @ Bc_T)
        d2 = np.maximum(d2, 0.0)

        # Khử sai số triệt tiêu cho các cặp rất gần nhau hoặc trùng lặp
        if kiem_tra_gan or scale_max >= 1e4:
            if scale_max >= 1e4:
                nguong_gan = 1e-8 * (a2[i0:i1, None] + b2[None, :] + 1.0)
                r_idx, c_idx = np.where(d2 <= nguong_gan)
            else:
                r_idx, c_idx = np.where(d2 <= 1e-12)
            if len(r_idx) > 0:
                diff = A_arr[i0 + r_idx] - B_arr[c_idx]
                d2[r_idx, c_idx] = np.sum(diff * diff, axis=1)

        if tu_doi_xung:
            hang = np.arange(i1 - i0)
            d2[hang, i0 + hang] = 0.0

        khoi = d2 if binh_phuong else np.sqrt(d2)
        yield i0, i1, khoi


def ma_tran_khoang_cach(
    X: np.ndarray,
    co_khoi: int = 1024,
    max_n: int | None = 6000,
) -> np.ndarray:
    """Tính ma trận khoảng cách Euclid n×n dạng float64 (khuyến nghị n <= 5.000)."""
    X_arr = np.asarray(X, dtype=np.float64)
    n = len(X_arr)
    if max_n is not None and n > max_n:
        du_kien_gb = (n * n * 8) / 1e9
        raise MemoryError(
            f"Không dựng ma trận {n}×{n} (~{du_kien_gb:.2f} GB) vượt quá giới hạn max_n={max_n}."
        )

    D = np.empty((n, n), dtype=np.float64)
    for i0, i1, khoi in euclid_theo_khoi(X_arr, None, co_khoi=co_khoi, binh_phuong=False):
        D[i0:i1] = khoi

    np.fill_diagonal(D, 0.0)
    D = 0.5 * (D + D.T)
    np.fill_diagonal(D, 0.0)
    return D


def gan_gan_nhat(
    X: np.ndarray,
    tam: np.ndarray,
    co_khoi: int = 4096,
) -> tuple[np.ndarray, np.ndarray]:
    """Gán mỗi điểm trong X vào tâm/medoid gần nhất, trả về (nhan, d_min)."""
    X_arr = np.asarray(X, dtype=np.float64)
    tam_arr = np.asarray(tam, dtype=np.float64)
    n = len(X_arr)

    nhan = np.empty(n, dtype=np.int64)
    d_min = np.empty(n, dtype=np.float64)

    for i0, i1, khoi in euclid_theo_khoi(X_arr, tam_arr, co_khoi=co_khoi, binh_phuong=False):
        chi_so = np.argmin(khoi, axis=1)
        nhan[i0:i1] = chi_so
        d_min[i0:i1] = khoi[np.arange(i1 - i0), chi_so]

    return nhan, d_min


def silhouette_theo_khoi(
    X: np.ndarray,
    nhan: np.ndarray,
    co_khoi: int = 1024,
) -> tuple[np.ndarray, float]:
    """Tính hệ số bóng từng điểm và trung bình với bộ nhớ O(co_khoi × n)."""
    X_arr = np.asarray(X, dtype=np.float64)
    nhan_arr = np.asarray(nhan)
    n = len(X_arr)
    if n == 0:
        return np.array([], dtype=np.float64), 0.0

    _, inv = np.unique(nhan_arr, return_inverse=True)
    k = int(inv.max()) + 1
    if k < 2 or n < 2:
        s_zero = np.zeros(n, dtype=np.float64)
        return s_zero, 0.0

    counts = np.bincount(inv, minlength=k).astype(np.float64)
    one_hot = np.eye(k, dtype=np.float64)[inv]  # (n, k)
    s_i = np.zeros(n, dtype=np.float64)

    for i0, i1, khoi in euclid_theo_khoi(X_arr, None, co_khoi=co_khoi, binh_phuong=False):
        m = i1 - i0
        tong_cum = khoi @ one_hot  # (m, k)
        g = inv[i0:i1]
        hang = np.arange(m)

        so_cung = counts[g]
        a = np.zeros(m, dtype=np.float64)
        nhieu_hon_1 = so_cung > 1.0
        a[nhieu_hon_1] = tong_cum[hang[nhieu_hon_1], g[nhieu_hon_1]] / (so_cung[nhieu_hon_1] - 1.0)

        tb_cac_cum = tong_cum / counts[None, :]
        tb_cac_cum[hang, g] = np.inf
        b = np.min(tb_cac_cum, axis=1)

        mau = np.maximum(a, b)
        s_khoi = np.zeros(m, dtype=np.float64)
        hop_le = nhieu_hon_1 & (mau > 0.0)
        s_khoi[hop_le] = (b[hop_le] - a[hop_le]) / mau[hop_le]
        s_i[i0:i1] = s_khoi

    return s_i, float(np.mean(s_i))


def silhouette_nhieu_phan_hoach(
    X: np.ndarray,
    ds_nhan: Sequence[np.ndarray],
    co_khoi: int = 1024,
) -> list[float]:
    """Tính đồng thời silhouette trung bình cho nhiều phân hoạch trên cùng X trong 1 lượt quét khối."""
    X_arr = np.asarray(X, dtype=np.float64)
    n = len(X_arr)
    if not ds_nhan:
        return []
    if n < 2:
        return [0.0 for _ in ds_nhan]

    ket_qua = [0.0 for _ in ds_nhan]
    meta: list[tuple[int, np.ndarray, np.ndarray, int, int]] = []
    cac_one_hot: list[np.ndarray] = []
    offset = 0

    for idx_ph, nhan in enumerate(ds_nhan):
        _, inv = np.unique(np.asarray(nhan), return_inverse=True)
        k = int(inv.max()) + 1
        if k < 2:
            continue
        counts = np.bincount(inv, minlength=k).astype(np.float64)
        cac_one_hot.append(np.eye(k, dtype=np.float64)[inv])
        meta.append((idx_ph, inv, counts, offset, offset + k))
        offset += k

    if not meta:
        return ket_qua

    one_hot_tong = np.hstack(cac_one_hot)  # (n, sum_k)
    tong_s = np.zeros(len(meta), dtype=np.float64)

    for i0, i1, khoi in euclid_theo_khoi(X_arr, None, co_khoi=co_khoi, binh_phuong=False):
        m = i1 - i0
        hang = np.arange(m)
        tong_all = khoi @ one_hot_tong

        for j, (_, inv, counts, c0, c1) in enumerate(meta):
            tong_cum = tong_all[:, c0:c1]
            g = inv[i0:i1]
            so_cung = counts[g]
            a = np.zeros(m, dtype=np.float64)
            nhieu_hon_1 = so_cung > 1.0
            a[nhieu_hon_1] = tong_cum[hang[nhieu_hon_1], g[nhieu_hon_1]] / (so_cung[nhieu_hon_1] - 1.0)

            tb_cac_cum = tong_cum / counts[None, :]
            tb_cac_cum[hang, g] = np.inf
            b = np.min(tb_cac_cum, axis=1)

            mau = np.maximum(a, b)
            s_khoi = np.zeros(m, dtype=np.float64)
            hop_le = nhieu_hon_1 & (mau > 0.0)
            s_khoi[hop_le] = (b[hop_le] - a[hop_le]) / mau[hop_le]
            tong_s[j] += float(np.sum(s_khoi))

    for j, (idx_ph, _, _, _, _) in enumerate(meta):
        ket_qua[idx_ph] = float(tong_s[j] / n)

    return ket_qua


def do_bo_nho(
    cac_n: Sequence[int] = (1000, 2000, 3000, 5000),
    d: int = 16,
    co_khoi: int = 1024,
    duong_dan_luu: Path | str | None = DEFAULT_MEMORY_CSV,
) -> pd.DataFrame:
    """Đo bộ nhớ thực tế (psutil RSS) khi dựng ma trận khoảng cách n×n float64."""
    from experiments.cau_hinh import HAT_GIONG

    proc = psutil.Process(os.getpid())
    rng = np.random.default_rng(HAT_GIONG)
    ket_qua = []

    for n in cac_n:
        n_int = int(n)
        X_tmp = rng.normal(size=(n_int, d))
        gc.collect()
        rss_truoc = proc.memory_info().rss
        D = ma_tran_khoang_cach(X_tmp, co_khoi=co_khoi, max_n=None)
        # Chạm toàn bộ vùng nhớ để hệ điều hành ghi nhận RSS thực tế
        _ = float(D[0, 0] + D[-1, -1])
        rss_sau = proc.memory_info().rss
        ram_con_trong = psutil.virtual_memory().available

        byte_ly_thuyet = n_int * n_int * 8
        rss_chenh = max(rss_sau - rss_truoc, 0)

        ket_qua.append(
            {
                "n": n_int,
                "byte_ly_thuyet": byte_ly_thuyet,
                "mb_ly_thuyet": round(byte_ly_thuyet / (1024 ** 2), 2),
                "rss_do_duoc": rss_chenh,
                "mb_rss_do_duoc": round(rss_chenh / (1024 ** 2), 2),
                "rss_tong_tien_trinh": rss_sau,
                "ram_con_trong": ram_con_trong,
                "gb_ram_con_trong": round(ram_con_trong / (1024 ** 3), 2),
            }
        )
        del D, X_tmp
        gc.collect()

    df = pd.DataFrame(ket_qua)
    if duong_dan_luu is not None:
        out_path = Path(duong_dan_luu)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_path, index=False, encoding="utf-8-sig")

    return df

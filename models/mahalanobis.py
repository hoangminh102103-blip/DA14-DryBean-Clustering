from __future__ import annotations

from typing import Any, Iterator

import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment

from models.khoang_cach import euclid_theo_khoi
from models.pca import chieu, khop_pca


def nghich_dao_gia_svd(
    S: np.ndarray,
    nguong_cat: float = 1e-6,
    tikonov: float = 0.0,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    """Tính nghịch đảo giả Moore-Penrose (hoặc Tikhonov) của ma trận hiệp phương sai qua SVD.

    Trả về (S_inv, W_lam_trang, thong_tin) với tính chất S_inv = W_lam_trang.T @ W_lam_trang,
    nên khoảng cách Mahalanobis tương đương khoảng cách Euclid trên dữ liệu đã làm trắng X @ W.T.
    """
    S_arr = np.asarray(S, dtype=np.float64)
    S_sym = 0.5 * (S_arr + S_arr.T)
    U, s, Vt = np.linalg.svd(S_sym, full_matrices=False)

    s_max = float(s[0]) if len(s) > 0 else 0.0
    nguong_thuc = float(nguong_cat) * s_max if s_max > 0.0 else float(nguong_cat)

    s_inv = np.zeros_like(s)
    if tikonov > 0.0:
        giu_mask = s > 0.0
        s_inv[giu_mask] = 1.0 / (s[giu_mask] + float(tikonov))
    else:
        giu_mask = s > nguong_thuc
        s_inv[giu_mask] = 1.0 / s[giu_mask]

    S_inv = (Vt.T * s_inv[None, :]) @ U.T
    S_inv = 0.5 * (S_inv + S_inv.T)
    W_lam_trang = np.sqrt(s_inv)[:, None] * Vt  # (p, p)

    info = {
        "tri_ky_di": s,
        "so_chieu_giu": int(np.sum(giu_mask)),
        "so_chieu_cat": int(len(s) - np.sum(giu_mask)),
        "nguong_thuc": nguong_thuc,
        "tikonov": float(tikonov),
        "cond_S": float(np.linalg.cond(S_sym)),
    }
    return S_inv, W_lam_trang, info


def phan_ra_mahalanobis(
    X_tr: np.ndarray,
    nguong_cat: float = 1e-3,
    tikonov: float = 0.0,
) -> dict[str, Any]:
    """Ước lượng hiệp phương sai từ X_tr và phân rã sang ma trận làm trắng W."""
    X_arr = np.asarray(X_tr, dtype=np.float64)
    cov = np.cov(X_arr, rowvar=False)
    S_inv, W, info = nghich_dao_gia_svd(cov, nguong_cat=nguong_cat, tikonov=tikonov)
    return {
        "cov": cov,
        "S_inv": S_inv,
        "W": W,
        **info,
    }


def mahalanobis_theo_khoi(
    A: np.ndarray,
    B: np.ndarray | None,
    W_hoac_S_inv: np.ndarray,
    co_khoi: int = 1024,
    la_ma_tran_nghich_dao: bool = False,
) -> Iterator[tuple[int, int, np.ndarray]]:
    """Tính khoảng cách Mahalanobis theo khối từ ma trận nghịch đảo đã phân rã (hoặc S_inv)."""
    A_arr = np.asarray(A, dtype=np.float64)
    B_arr = A_arr if B is None else np.asarray(B, dtype=np.float64)
    M = np.asarray(W_hoac_S_inv, dtype=np.float64)

    if la_ma_tran_nghich_dao:
        # Phân rã S_inv = W^T W để chuyển thành Euclid trên không gian làm trắng
        eigvals, eigvecs = np.linalg.eigh(0.5 * (M + M.T))
        eigvals = np.maximum(eigvals, 0.0)
        W = np.sqrt(eigvals)[:, None] * eigvecs.T
    else:
        W = M

    Aw = A_arr @ W.T
    Bw = None if B is None else (B_arr @ W.T)
    yield from euclid_theo_khoi(Aw, Bw, co_khoi=co_khoi, binh_phuong=False)


def ma_tran_mahalanobis(
    X: np.ndarray,
    W_hoac_S_inv: np.ndarray,
    co_khoi: int = 1024,
    la_ma_tran_nghich_dao: bool = False,
) -> np.ndarray:
    """Dựng ma trận khoảng cách Mahalanobis n×n từ ma trận làm trắng W hoặc nghịch đảo S_inv."""
    X_arr = np.asarray(X, dtype=np.float64)
    n = len(X_arr)
    D = np.empty((n, n), dtype=np.float64)
    for i0, i1, khoi in mahalanobis_theo_khoi(
        X_arr,
        None,
        W_hoac_S_inv,
        co_khoi=co_khoi,
        la_ma_tran_nghich_dao=la_ma_tran_nghich_dao,
    ):
        D[i0:i1] = khoi
    np.fill_diagonal(D, 0.0)
    D = 0.5 * (D + D.T)
    np.fill_diagonal(D, 0.0)
    return D


def do_so_dieu_kien_pca(Z_tr: np.ndarray) -> pd.DataFrame:
    """Đo số điều kiện của ma trận hiệp phương sai theo số chiều PCA giữ lại (d = 1..p)."""
    Z_arr = np.asarray(Z_tr, dtype=np.float64)
    pca_mh = khop_pca(Z_arr)
    p = Z_arr.shape[1]
    dong = []
    for d in range(1, p + 1):
        Zd = chieu(pca_mh, Z_arr, d)
        cov_d = np.cov(Zd, rowvar=False) if d > 1 else np.array([[float(np.var(Zd, ddof=1))]])
        cond_cov = float(np.linalg.cond(cov_d))
        cond_z = float(np.linalg.cond(Zd))
        s_min = float(pca_mh["phuong_sai"][d - 1])
        s_max = float(pca_mh["phuong_sai"][0])
        dong.append(
            {
                "so_chieu_pca_d": d,
                "phuong_sai_tich_luy": float(np.sum(pca_mh["ty_le"][:d])),
                "phuong_sai_pc_cuoi": s_min,
                "cond_Z_d": cond_z,
                "cond_Cov_d": cond_cov,
                "ty_so_tri_rieng": s_max / max(s_min, 1e-18),
                "bat_on_dinh_tren_1e4": bool(cond_cov > 1e4),
            }
        )
    return pd.DataFrame(dong)


def can_chinh_nhan_hungarian(y_ref: np.ndarray, y_target: np.ndarray) -> np.ndarray:
    """Ánh xạ lại chỉ số cụm của y_target cho khớp tối đa với nhãn y_ref bằng Hungarian."""
    ua, ia = np.unique(y_ref, return_inverse=True)
    ub, ib = np.unique(y_target, return_inverse=True)
    m = max(len(ua), len(ub))
    bang = np.zeros((m, m), dtype=np.int64)
    np.add.at(bang, (ia, ib), 1)
    r_ind, c_ind = linear_sum_assignment(-bang)
    map_b_to_a = {int(c): int(r) for r, c in zip(r_ind, c_ind)}
    return np.array([map_b_to_a[int(v)] for v in ib], dtype=np.int64)


def so_sanh_ba_phan_hoach(
    nhan_dict: dict[str, np.ndarray],
    ari_fn,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Sinh ma trận trùng lặp 3×3 (ARI và % khớp sau canh nhãn) giữa 3 lối đo khoảng cách."""
    ten_list = list(nhan_dict.keys())
    m = len(ten_list)
    mat_ari = np.ones((m, m), dtype=np.float64)
    mat_pct = np.ones((m, m), dtype=np.float64)

    for i in range(m):
        for j in range(m):
            if i == j:
                continue
            ni = nhan_dict[ten_list[i]]
            nj = nhan_dict[ten_list[j]]
            mat_ari[i, j] = float(ari_fn(ni, nj))
            nj_aligned = can_chinh_nhan_hungarian(ni, nj)
            mat_pct[i, j] = float(np.mean(ni == nj_aligned))

    df_ari = pd.DataFrame(mat_ari, index=ten_list, columns=ten_list)
    df_pct = pd.DataFrame(mat_pct, index=ten_list, columns=ten_list)
    return df_ari, df_pct

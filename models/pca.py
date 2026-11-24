from __future__ import annotations

from typing import Any

import numpy as np


def _chuan_hoa_dau_svd(U: np.ndarray, Vt: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Chuẩn hóa dấu từng trục sao cho phần tử có trị tuyệt đối lớn nhất > 0."""
    max_abs_cols = np.argmax(np.abs(Vt), axis=1)
    signs = np.sign(Vt[np.arange(len(Vt)), max_abs_cols])
    signs[signs == 0.0] = 1.0
    Vt_moi = Vt * signs[:, None]
    U_moi = U * signs[None, :]
    return U_moi, Vt_moi


def khop_pca(Z_tr: np.ndarray) -> dict[str, Any]:
    """Khớp PCA bằng phân rã SVD tự viết trên tập huấn luyện đã chuẩn hóa."""
    Z = np.asarray(Z_tr, dtype=np.float64)
    n, p = Z.shape
    if n < 2:
        raise ValueError("Cần ít nhất 2 mẫu để khớp PCA.")

    # Bước 1: Trừ trung bình của tập huấn luyện
    mean = Z.mean(axis=0)
    Zc = Z - mean

    # Bước 2: Phân rã giá trị kỳ dị SVD
    U, S, Vt = np.linalg.svd(Zc, full_matrices=False)

    # Bước 3: Chuẩn hóa dấu trục để kết quả tái lập ổn định
    _, Vt = _chuan_hoa_dau_svd(U, Vt)

    # Bước 4: Phương sai giải thích và tỷ lệ phương sai
    phuong_sai = (S ** 2) / (n - 1)
    tong_ps = float(np.sum(phuong_sai))
    ty_le = phuong_sai / tong_ps if tong_ps > 0.0 else np.zeros_like(phuong_sai)

    return {
        "mean": mean,
        "Vt": Vt,
        "S": S,
        "phuong_sai": phuong_sai,
        "ty_le": ty_le,
        "n_mau": int(n),
        "n_dac_trung": int(p),
    }


def chieu(mo_hinh: dict[str, Any], X: np.ndarray, d: int) -> np.ndarray:
    """Chiếu dữ liệu X xuống d thành phần chính đầu tiên."""
    X_arr = np.asarray(X, dtype=np.float64)
    Vt = mo_hinh["Vt"]
    if d < 1 or d > len(Vt):
        raise ValueError(f"Số chiều d={d} phải nằm trong [1, {len(Vt)}].")
    return (X_arr - mo_hinh["mean"]) @ Vt[:d].T


def dung_nguoc(mo_hinh: dict[str, Any], Zd: np.ndarray, d: int) -> np.ndarray:
    """Dựng ngược dữ liệu từ không gian d chiều về lại không gian gốc."""
    Zd_arr = np.asarray(Zd, dtype=np.float64)
    Vt = mo_hinh["Vt"]
    if d < 1 or d > len(Vt):
        raise ValueError(f"Số chiều d={d} phải nằm trong [1, {len(Vt)}].")
    return Zd_arr @ Vt[:d] + mo_hinh["mean"]


def phuong_sai_tich_luy(mo_hinh: dict[str, Any]) -> np.ndarray:
    """Tính đường phương sai giải thích tích lũy (trong [0, 1])."""
    return np.cumsum(mo_hinh["ty_le"])


def k_giu(mo_hinh: dict[str, Any], nguong: float) -> int:
    """Tìm số thành phần chính tối thiểu để giữ tối thiểu ngưỡng phương sai."""
    thr = float(nguong) / 100.0 if float(nguong) > 1.0 else float(nguong)
    if thr <= 0.0:
        return 1
    if thr > 1.0:
        thr = 1.0
    tich_luy = phuong_sai_tich_luy(mo_hinh)
    idx = int(np.searchsorted(tich_luy, thr, side="left"))
    return min(idx + 1, len(tich_luy))

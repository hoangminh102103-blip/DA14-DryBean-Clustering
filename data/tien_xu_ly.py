from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from experiments.cau_hinh import HAT_GIONG as SEED_MAC_DINH

TEN_COT_MAC_DINH = (
    "Area",
    "Perimeter",
    "MajorAxisLength",
    "MinorAxisLength",
    "AspectRation",
    "Eccentricity",
    "ConvexArea",
    "EquivDiameter",
    "Extent",
    "Solidity",
    "roundness",
    "Compactness",
    "ShapeFactor1",
    "ShapeFactor2",
    "ShapeFactor3",
    "ShapeFactor4",
)


def chia_phan_tang(
    X: pd.DataFrame | np.ndarray,
    y: pd.Series | np.ndarray,
    ty_le_test: float = 0.2,
    seed: int = SEED_MAC_DINH,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Chia phân tầng tập dữ liệu trước khi khớp bất kỳ phép biến đổi nào."""
    X_arr = np.asarray(X, dtype=np.float64)
    y_arr = np.asarray(y)
    n = len(y_arr)
    if len(X_arr) != n:
        raise ValueError(f"Số dòng của X ({len(X_arr)}) không khớp y ({n}).")

    idx_all = np.arange(n, dtype=np.int64)
    idx_tr, idx_te = train_test_split(
        idx_all,
        test_size=ty_le_test,
        stratify=y_arr,
        random_state=int(seed),
    )
    return (
        X_arr[idx_tr],
        X_arr[idx_te],
        y_arr[idx_tr],
        y_arr[idx_te],
        idx_tr,
        idx_te,
    )


def khop_chuan_hoa(X_tr: pd.DataFrame | np.ndarray) -> StandardScaler:
    """Khớp StandardScaler chỉ trên tập huấn luyện để chống rò rỉ dữ liệu."""
    X_arr = np.asarray(X_tr, dtype=np.float64)
    return StandardScaler().fit(X_arr)


def ap_chuan_hoa(scaler: StandardScaler, X: pd.DataFrame | np.ndarray) -> np.ndarray:
    """Áp dụng StandardScaler đã khớp cho tập dữ liệu đầu vào."""
    X_arr = np.asarray(X, dtype=np.float64)
    return scaler.transform(X_arr)


def chuan_bi(
    X: pd.DataFrame | np.ndarray,
    y: pd.Series | np.ndarray,
    seed: int = SEED_MAC_DINH,
    chuan_hoa: bool = True,
    ty_le_test: float = 0.2,
) -> dict[str, Any]:
    """Chia phân tầng 80/20 trước, sau đó mới chuẩn hóa (hoặc giữ thô cho baseline)."""
    X_tr, X_te, y_tr, y_te, idx_tr, idx_te = chia_phan_tang(
        X, y, ty_le_test=ty_le_test, seed=seed
    )
    if chuan_hoa:
        scaler = khop_chuan_hoa(X_tr)
        Z_tr = ap_chuan_hoa(scaler, X_tr)
        Z_te = ap_chuan_hoa(scaler, X_te)
    else:
        scaler = None
        Z_tr = X_tr.copy()
        Z_te = X_te.copy()

    return {
        "X_tr": X_tr,
        "X_te": X_te,
        "y_tr": y_tr,
        "y_te": y_te,
        "scaler": scaler,
        "Z_tr": Z_tr,
        "Z_te": Z_te,
        "idx_tr": idx_tr,
        "idx_te": idx_te,
    }


def lay_mau_con(
    y_tr: pd.Series | np.ndarray,
    n_mau: int = 3000,
    seed: int = SEED_MAC_DINH,
) -> np.ndarray:
    """Lấy mẫu con phân tầng từ tập huấn luyện, trả về mảng chỉ số."""
    y_arr = np.asarray(y_tr)
    n = len(y_arr)
    if n_mau <= 0:
        raise ValueError("n_mau phải lớn hơn 0.")
    if n_mau >= n:
        return np.arange(n, dtype=np.int64)

    idx_mau, _ = train_test_split(
        np.arange(n, dtype=np.int64),
        train_size=int(n_mau),
        stratify=y_arr,
        random_state=int(seed),
    )
    return idx_mau


def _giai_ma_chi_so_cot(X_tr: pd.DataFrame | np.ndarray, cot: str | int) -> int:
    if isinstance(cot, (int, np.integer)):
        col_idx = int(cot)
        n_cols = X_tr.shape[1]
        if col_idx < 0 or col_idx >= n_cols:
            raise IndexError(f"Chỉ số cột {col_idx} nằm ngoài [0, {n_cols - 1}].")
        return col_idx
    if isinstance(X_tr, pd.DataFrame):
        if cot not in X_tr.columns:
            raise KeyError(f"Không tìm thấy cột '{cot}' trong DataFrame.")
        return int(X_tr.columns.get_loc(cot))
    if cot in TEN_COT_MAC_DINH:
        return TEN_COT_MAC_DINH.index(cot)
    raise KeyError(f"Không biết ánh xạ cột '{cot}' sang chỉ số mảng NumPy.")


def tiem_ngoai_lai(
    X_tr: pd.DataFrame | np.ndarray,
    ty_le: float = 0.01,
    he_so: tuple[float, float] | float = (8.0, 12.0),
    cot: str | int = "Area",
    seed: int = SEED_MAC_DINH,
) -> tuple[pd.DataFrame | np.ndarray, dict[str, Any]]:
    """Tiêm ngoại lai nhân tạo trên bản sao dữ liệu thô, không sửa tại chỗ."""
    n = len(X_tr)
    so_luong = int(round(ty_le * n))
    if so_luong < 0 or so_luong > n:
        raise ValueError(f"Số lượng điểm tiêm ({so_luong}) không hợp lệ với n={n}.")

    col_idx = _giai_ma_chi_so_cot(X_tr, cot)
    rng = np.random.default_rng(int(seed))
    idx = np.sort(rng.choice(n, size=so_luong, replace=False)).astype(np.int64)

    if isinstance(he_so, (tuple, list, np.ndarray)):
        if len(he_so) != 2:
            raise ValueError("he_so dạng khoảng phải có đúng 2 phần tử (min, max).")
        cac_he_so = rng.uniform(float(he_so[0]), float(he_so[1]), size=so_luong)
    else:
        cac_he_so = np.full(so_luong, float(he_so), dtype=np.float64)

    if isinstance(X_tr, pd.DataFrame):
        X_moi = X_tr.copy(deep=True)
        col_name = X_moi.columns[col_idx]
        X_moi.iloc[idx, col_idx] = X_moi.iloc[idx, col_idx].to_numpy(dtype=np.float64) * cac_he_so
        cot_ten = str(col_name)
    else:
        X_moi = np.array(X_tr, dtype=np.float64, copy=True)
        X_moi[idx, col_idx] = X_moi[idx, col_idx] * cac_he_so
        cot_ten = str(cot)

    info = {
        "idx": idx,
        "he_so": cac_he_so,
        "cot": cot_ten,
        "col_idx": col_idx,
        "seed": int(seed),
    }
    return X_moi, info


def ma_hoa_nhan(y: pd.Series | np.ndarray) -> tuple[np.ndarray, list[str]]:
    """Mã hóa nhãn chuỗi sang số nguyên 0..C-1 theo thứ tự chữ cái."""
    y_arr = np.asarray(y).astype(str)
    ten_lop, y_int = np.unique(y_arr, return_inverse=True)
    return y_int.astype(np.int64), ten_lop.tolist()

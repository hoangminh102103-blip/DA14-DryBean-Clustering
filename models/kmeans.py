from __future__ import annotations

from typing import Any

import numpy as np

from models.khoang_cach import gan_gan_nhat


def kmeanspp(X: np.ndarray, k: int, rng: np.random.Generator) -> np.ndarray:
    """Khởi tạo k tâm cụm theo k-means++ với xác suất tỷ lệ thuận D²."""
    X_arr = np.asarray(X, dtype=np.float64)
    n, d = X_arr.shape
    if k < 1 or k > n:
        raise ValueError(f"k={k} không hợp lệ với n={n}.")

    tam = np.empty((k, d), dtype=np.float64)
    idx0 = int(rng.integers(0, n))
    tam[0] = X_arr[idx0]
    d2_min = np.sum((X_arr - tam[0]) ** 2, axis=1)

    for c in range(1, k):
        tong = float(np.sum(d2_min))
        if tong <= 0.0:
            idx = int(rng.integers(0, n))
        else:
            tich_luy = np.cumsum(d2_min)
            nguong = rng.random() * float(tich_luy[-1])
            idx = min(int(np.searchsorted(tich_luy, nguong, side="right")), n - 1)
        tam[c] = X_arr[idx]
        d2_moi = np.sum((X_arr - tam[c]) ** 2, axis=1)
        d2_min = np.minimum(d2_min, d2_moi)

    return tam


def gan_cum(
    X: np.ndarray,
    tam: np.ndarray,
    co_khoi: int = 4096,
) -> tuple[np.ndarray, np.ndarray]:
    """Gán cụm theo khoảng cách Euclid và trả về (nhan, d2_min)."""
    nhan, d_min = gan_gan_nhat(X, tam, co_khoi=co_khoi)
    return nhan, d_min * d_min


def cap_nhat_tam(
    X: np.ndarray,
    nhan: np.ndarray,
    k: int,
    tam_cu: np.ndarray,
    rng: np.random.Generator,
) -> np.ndarray:
    """Cập nhật tâm trung bình từng cụm; xử lý cụm rỗng bằng điểm xa tâm nhất."""
    X_arr = np.asarray(X, dtype=np.float64)
    tam_moi = np.empty((k, X_arr.shape[1]), dtype=np.float64)

    cum_rong: list[int] = []
    for c in range(k):
        mask = nhan == c
        if np.any(mask):
            tam_moi[c] = X_arr[mask].mean(axis=0)
        else:
            cum_rong.append(c)

    if cum_rong:
        d2_hien_tai = np.sum((X_arr - tam_cu[nhan]) ** 2, axis=1)
        thu_tu_xa = np.argsort(d2_hien_tai)[::-1]
        da_chon = set()
        for c in cum_rong:
            chon = None
            for idx in thu_tu_xa:
                idx_int = int(idx)
                if idx_int not in da_chon:
                    chon = idx_int
                    da_chon.add(idx_int)
                    break
            if chon is None:
                chon = int(rng.integers(0, len(X_arr)))
            tam_moi[c] = X_arr[chon]

    return tam_moi


def kmeans(
    X: np.ndarray,
    k: int,
    n_init: int = 10,
    max_iter: int = 300,
    tol: float = 1e-4,
    seed: int = 0,
    init: np.ndarray | None = None,
) -> dict[str, Any]:
    """Thuật toán k-means (Lloyd + k-means++) tự viết bằng NumPy."""
    X_arr = np.asarray(X, dtype=np.float64)
    n, d = X_arr.shape
    if k < 1 or k > n:
        raise ValueError(f"k={k} không hợp lệ với n={n}.")

    rng = np.random.default_rng(int(seed))
    var_tb = float(np.mean(np.var(X_arr, axis=0)))
    tol_hieu_dung = float(tol) * max(var_tb, 1e-12)

    so_lan = 1 if init is not None else max(1, int(n_init))
    best_ket_qua: dict[str, Any] | None = None

    for lan in range(so_lan):
        if init is not None and lan == 0:
            tam = np.array(init, dtype=np.float64, copy=True)
            if tam.shape != (k, d):
                raise ValueError(f"init có kích thước {tam.shape}, kỳ vọng ({k}, {d}).")
        else:
            tam = kmeanspp(X_arr, k, rng)

        nhan_cu: np.ndarray | None = None
        lich_su_sse: list[float] = []
        n_iter = 0

        for it in range(1, int(max_iter) + 1):
            nhan, d2_min = gan_cum(X_arr, tam)
            sse = float(np.sum(d2_min))
            lich_su_sse.append(sse)
            n_iter = it

            if nhan_cu is not None and np.array_equal(nhan, nhan_cu):
                break

            tam_moi = cap_nhat_tam(X_arr, nhan, k, tam, rng)
            dich_chuyen = float(np.sum((tam_moi - tam) ** 2))
            tam = tam_moi
            nhan_cu = nhan

            if dich_chuyen <= tol_hieu_dung:
                break

        # Đồng bộ nhãn và SSE cuối cùng theo tâm vừa cập nhật
        nhan_cuoi, d2_cuoi = gan_cum(X_arr, tam)
        sse_cuoi = float(np.sum(d2_cuoi))
        if not lich_su_sse or sse_cuoi < lich_su_sse[-1] - 1e-12:
            lich_su_sse.append(sse_cuoi)

        if best_ket_qua is None or sse_cuoi < best_ket_qua["sse"]:
            best_ket_qua = {
                "tam": tam,
                "nhan": nhan_cuoi,
                "sse": sse_cuoi,
                "n_iter": n_iter,
                "lich_su_sse": lich_su_sse,
            }

    assert best_ket_qua is not None
    return best_ket_qua

from __future__ import annotations

from typing import Any

import numpy as np

from data.tien_xu_ly import lay_mau_con
from models.khoang_cach import gan_gan_nhat, ma_tran_khoang_cach


def chi_phi(D: np.ndarray, medoid: list[int] | np.ndarray) -> float:
    """Tổng khoảng cách từ mọi điểm tới medoid gần nhất."""
    return float(D[:, medoid].min(axis=1).sum())


def build(D: np.ndarray, k: int) -> list[int]:
    """Pha BUILD của PAM: chọn tham lam k medoid giúp giảm tổng chi phí nhiều nhất."""
    D_arr = np.asarray(D, dtype=np.float64)
    n = D_arr.shape[0]
    if k < 1 or k > n:
        raise ValueError(f"k={k} không hợp lệ với n={n}.")

    m0 = int(np.argmin(D_arr.sum(axis=1)))
    medoids = [m0]
    d_gan_nhat = D_arr[:, m0].copy()

    for _ in range(1, k):
        do_loi = np.maximum(d_gan_nhat[:, None] - D_arr, 0.0).sum(axis=0)
        do_loi[medoids] = -np.inf
        ung_vien = int(np.argmax(do_loi))
        medoids.append(ung_vien)
        d_gan_nhat = np.minimum(d_gan_nhat, D_arr[:, ung_vien])

    return medoids


def swap_tho(
    D: np.ndarray,
    medoid: list[int] | np.ndarray,
    max_iter: int = 500,
) -> tuple[list[int], float, list[float]]:
    """Pha SWAP ngây thơ tính lại chi_phi cho mọi cặp (chỉ làm oracle kiểm thử)."""
    D_arr = np.asarray(D, dtype=np.float64)
    n = D_arr.shape[0]
    hien_tai = list(map(int, medoid))
    chi_phi_ht = chi_phi(D_arr, hien_tai)
    lich_su = [chi_phi_ht]

    for _ in range(int(max_iter)):
        medoid_set = set(hien_tai)
        best_delta = 0.0
        best_swap: tuple[int, int] | None = None

        for r in range(len(hien_tai)):
            for h in range(n):
                if h in medoid_set:
                    continue
                thu = list(hien_tai)
                thu[r] = h
                chi_phi_moi = chi_phi(D_arr, thu)
                delta = chi_phi_moi - chi_phi_ht
                if delta < best_delta - 1e-12:
                    best_delta = delta
                    best_swap = (r, h)

        if best_swap is None:
            break

        r_chon, h_chon = best_swap
        hien_tai[r_chon] = h_chon
        chi_phi_ht = chi_phi(D_arr, hien_tai)
        if chi_phi_ht >= lich_su[-1] - 1e-12:
            break
        lich_su.append(chi_phi_ht)

    return hien_tai, chi_phi_ht, lich_su


def swap(
    D: np.ndarray,
    medoid: list[int] | np.ndarray,
    max_iter: int = 500,
) -> tuple[list[int], float, list[float]]:
    """Pha SWAP vector hóa O(k·n²) chọn phép hoán đổi giảm chi phí nhiều nhất mỗi vòng."""
    D_arr = np.asarray(D, dtype=np.float64)
    n = D_arr.shape[0]
    hien_tai = list(map(int, medoid))
    k = len(hien_tai)
    chi_phi_ht = chi_phi(D_arr, hien_tai)
    lich_su = [chi_phi_ht]

    if k == 1:
        tong_cot = D_arr.sum(axis=0)
        for _ in range(int(max_iter)):
            ung_vien_cost = tong_cot.copy()
            ung_vien_cost[hien_tai[0]] = np.inf
            h_chon = int(np.argmin(ung_vien_cost))
            if ung_vien_cost[h_chon] - chi_phi_ht < -1e-12:
                hien_tai[0] = h_chon
                chi_phi_ht = chi_phi(D_arr, hien_tai)
                if chi_phi_ht >= lich_su[-1] - 1e-12:
                    break
                lich_su.append(chi_phi_ht)
            else:
                break
        return hien_tai, chi_phi_ht, lich_su

    rows = np.arange(n)
    buf = np.empty_like(D_arr)
    for _ in range(int(max_iter)):
        D_m = D_arr[:, hien_tai]  # (n, k)
        # Dùng argpartition kth=1 lấy đồng thời medoid gần nhất và gần thứ hai
        part = np.argpartition(D_m, kth=1, axis=1)[:, :2]
        c1 = part[:, 0]
        c2 = part[:, 1]
        d1 = D_m[rows, c1]
        d2 = D_m[rows, c2]

        # Độ lợi thuần khi thêm điểm h nếu chưa loại bỏ medoid nào (tính tại chỗ trên buf)
        np.subtract(d1[:, None], D_arr, out=buf)
        np.maximum(buf, 0.0, out=buf)
        gain = buf.sum(axis=0)  # (n,)

        delta_mat = np.empty((k, n), dtype=np.float64)
        for r in range(k):
            mask = c1 == r
            m_r = int(np.count_nonzero(mask))
            if m_r > 0:
                D_r = D_arr[mask, :]
                b_view = buf[:m_r]
                np.minimum(d2[mask, None], D_r, out=b_view)
                delta_mat[r] = -gain + b_view.sum(axis=0)
                np.minimum(d1[mask, None], D_r, out=b_view)
                delta_mat[r] -= b_view.sum(axis=0)
            else:
                delta_mat[r] = -gain

        delta_mat[:, hien_tai] = np.inf
        flat_best = int(np.argmin(delta_mat))
        r_chon, h_chon = divmod(flat_best, n)
        best_delta = float(delta_mat[r_chon, h_chon])

        if best_delta >= -1e-12:
            break

        hien_tai[r_chon] = h_chon
        chi_phi_moi = chi_phi(D_arr, hien_tai)
        if chi_phi_moi >= chi_phi_ht - 1e-12:
            break
        chi_phi_ht = chi_phi_moi
        lich_su.append(chi_phi_ht)

    return hien_tai, chi_phi_ht, lich_su


def pam(
    D: np.ndarray,
    k: int,
    init: list[int] | np.ndarray | None = None,
    max_iter: int = 500,
) -> dict[str, Any]:
    """Thuật toán k-medoids PAM hai pha (BUILD + SWAP) tự viết bằng NumPy."""
    D_arr = np.asarray(D, dtype=np.float64)
    n = D_arr.shape[0]
    if k < 1 or k > n:
        raise ValueError(f"k={k} không hợp lệ với n={n}.")

    medoids_0 = build(D_arr, k) if init is None else list(map(int, init))
    medoids, chi_phi_cuoi, lich_su = swap(D_arr, medoids_0, max_iter=max_iter)
    nhan = np.argmin(D_arr[:, medoids], axis=1).astype(np.int64)

    return {
        "medoid": medoids,
        "nhan": nhan,
        "chi_phi": float(chi_phi_cuoi),
        "lich_su_chi_phi": lich_su,
        "n_swap": len(lich_su) - 1,
    }


def gan_medoid(
    X: np.ndarray,
    X_medoid: np.ndarray,
    co_khoi: int = 4096,
) -> np.ndarray:
    """Gán các điểm dữ liệu ngoài mẫu con về medoid gần nhất."""
    nhan, _ = gan_gan_nhat(X, X_medoid, co_khoi=co_khoi)
    return nhan


def clara(
    X: np.ndarray,
    k: int,
    n_mau: int = 3000,
    so_lan: int = 5,
    seed: int = 0,
    y: np.ndarray | None = None,
) -> dict[str, Any]:
    """Biến thể CLARA: chạy PAM trên nhiều mẫu con và chọn bộ medoid có chi phí toàn cục thấp nhất."""
    X_arr = np.asarray(X, dtype=np.float64)
    n = len(X_arr)
    rng = np.random.default_rng(int(seed))
    best_res: dict[str, Any] | None = None

    for lan in range(int(so_lan)):
        if y is not None:
            idx_sub = lay_mau_con(y, n_mau=min(n_mau, n), seed=int(seed) + lan)
        else:
            m = min(n_mau, n)
            idx_sub = np.sort(rng.choice(n, size=m, replace=False)).astype(np.int64)

        D_sub = ma_tran_khoang_cach(X_arr[idx_sub])
        res_sub = pam(D_sub, k)
        med_toan_cuc = idx_sub[res_sub["medoid"]].tolist()
        nhan_all, d_min_all = gan_gan_nhat(X_arr, X_arr[med_toan_cuc])
        tong_chi_phi = float(np.sum(d_min_all))

        if best_res is None or tong_chi_phi < best_res["chi_phi"]:
            best_res = {
                "medoid": med_toan_cuc,
                "nhan": nhan_all,
                "chi_phi": tong_chi_phi,
                "lich_su_chi_phi": res_sub["lich_su_chi_phi"],
                "n_swap": res_sub["n_swap"],
            }

    assert best_res is not None
    return best_res

from itertools import combinations
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy.optimize import linear_sum_assignment

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from data.nap import doc_va_kiem_ke
from data.tien_xu_ly import chuan_bi, lay_mau_con
from models.khoang_cach import ma_tran_khoang_cach
from models.kmeans import kmeans
from models.pam import build, chi_phi, gan_medoid, pam, swap, swap_tho


def _ty_le_trung_hoan_vi(y_a: np.ndarray, y_b: np.ndarray) -> float:
    ua, ia = np.unique(y_a, return_inverse=True)
    ub, ib = np.unique(y_b, return_inverse=True)
    m = max(len(ua), len(ub))
    cost = np.zeros((m, m), dtype=np.int64)
    np.add.at(cost, (ia, ib), 1)
    r_ind, c_ind = linear_sum_assignment(-cost)
    return float(cost[r_ind, c_ind].sum()) / float(len(y_a))


def test_vi_du_tay_6_hat_k2():
    """Ví dụ tay 6 hạt / 3 đặc trưng / k=2 (BUILD, 1 bước SWAP, so k-means & ngoại lai ×10)."""
    X = np.array(
        [
            [-3.2, -0.1, 0.1],   # Hạt 0 (nhóm 1)
            [-3.0, 0.0, 0.0],    # Hạt 1 (tâm nhóm 1)
            [-2.8, 0.1, -0.1],   # Hạt 2 (nhóm 1)
            [2.8, -0.1, -0.1],   # Hạt 3 (nhóm 2)
            [3.0, 0.0, 0.0],     # Hạt 4 (tâm nhóm 2)
            [3.2, 0.3, 0.1],     # Hạt 5 (nhóm 2)
        ],
        dtype=np.float64,
    )
    D = ma_tran_khoang_cach(X, co_khoi=6)
    assert D.shape == (6, 6)

    # (a) BUILD k=2: chọn 2 medoid khởi tạo
    med_build = build(D, k=2)
    cost_build = chi_phi(D, med_build)
    assert len(med_build) == 2

    # (b) Thực hiện 1 bước SWAP: so chi phí BUILD với nghiệm cuối {1, 4}
    res_pam = pam(D, k=2)
    assert set(res_pam["medoid"]) == {1, 4}
    assert res_pam["chi_phi"] <= cost_build + 1e-12
    # Kiểm chứng phép thử đổi 1 medoid sang hạt 0 (tăng chi phí -> từ chối)
    thu_tu_choi = [0 if m == 1 else m for m in res_pam["medoid"]]
    assert chi_phi(D, thu_tu_choi) > res_pam["chi_phi"] + 1e-12

    # (c) Tâm trung bình k-means trên cùng 2 cụm & so chi phí tuyến tính vs SSE
    nhan_pam = res_pam["nhan"]
    tam_km = np.vstack([X[nhan_pam == c].mean(axis=0) for c in range(2)])
    chi_phi_tuyen_tinh_km = float(
        sum(np.linalg.norm(X[i] - tam_km[nhan_pam[i]]) for i in range(6))
    )
    sse_km = float(sum(np.sum((X[i] - tam_km[nhan_pam[i]]) ** 2) for i in range(6)))
    sse_pam = float(
        sum(np.sum((X[i] - X[res_pam["medoid"][nhan_pam[i]]]) ** 2) for i in range(6))
    )
    # Medoid tối thiểu hóa tổng khoảng cách tuyến tính; centroid tối thiểu hóa SSE
    assert res_pam["chi_phi"] <= chi_phi_tuyen_tinh_km + 1e-12
    assert sse_km <= sse_pam + 1e-12

    # (d) Tiêm ngoại lai: nhân cột 1 của hạt 5 lên ×10 (0.3 -> 3.0)
    X_out = X.copy()
    X_out[5, 1] *= 10.0
    D_out = ma_tran_khoang_cach(X_out, co_khoi=6)
    res_pam_out = pam(D_out, k=2)
    res_km_out = kmeans(X_out, k=2, init=tam_km)

    # Tâm k-means bị kéo lệch, còn medoid của PAM giữ nguyên hai hạt thật {1, 4}
    med_sach_sorted = sorted(res_pam["medoid"])
    med_out_sorted = sorted(res_pam_out["medoid"])
    assert med_out_sorted == med_sach_sorted == [1, 4]

    tam_sach_sorted = tam_km[np.argsort(tam_km[:, 0])]
    tam_out_sorted = res_km_out["tam"][np.argsort(res_km_out["tam"][:, 0])]
    dich_chuyen_km = float(np.max(np.linalg.norm(tam_out_sorted - tam_sach_sorted, axis=1)))
    dich_chuyen_med = float(
        np.max(np.linalg.norm(X[med_out_sorted] - X[med_sach_sorted], axis=1))
    )
    assert dich_chuyen_km > 0.8
    assert dich_chuyen_med == 0.0


def test_swap_vector_hoa_khop_swap_tho_20_bo():
    rng = np.random.default_rng(2026)
    for lan in range(20):
        X = rng.normal(size=(60, 6))
        D = ma_tran_khoang_cach(X, co_khoi=32)
        k = [2, 4, 7][lan % 3]
        init_m = build(D, k)

        m_fast, c_fast, hist_fast = swap(D, init_m)
        m_tho, c_tho, hist_tho = swap_tho(D, init_m)

        assert m_fast == m_tho
        assert np.isclose(c_fast, c_tho, atol=1e-12)
        assert np.allclose(hist_fast, hist_tho, atol=1e-12)


def test_lich_su_chi_phi_giam_nghiem_ngat_va_rang_buoc_cum():
    rng = np.random.default_rng(77)
    X = rng.normal(size=(120, 8))
    D = ma_tran_khoang_cach(X, co_khoi=64)

    m_build = build(D, k=5)
    c_build = chi_phi(D, m_build)
    res = pam(D, k=5)

    assert c_build >= res["chi_phi"] - 1e-12
    assert np.all(np.diff(res["lich_su_chi_phi"]) < 0.0)
    assert res["lich_su_chi_phi"][-1] == pytest.approx(res["chi_phi"], abs=1e-12)

    # Mỗi medoid thuộc chính cụm của nó
    for c_idx, m_idx in enumerate(res["medoid"]):
        assert res["nhan"][m_idx] == c_idx

    # Tái lập khi chạy lại trên cùng D
    res2 = pam(D, k=5)
    assert res["medoid"] == res2["medoid"]
    assert np.array_equal(res["nhan"], res2["nhan"])


def test_vet_can_c_12_3():
    rng = np.random.default_rng(11)
    X_rand = rng.normal(size=(12, 4))
    D_rand = ma_tran_khoang_cach(X_rand)
    res_rand = pam(D_rand, k=3)
    opt_rand = min(chi_phi(D_rand, list(c)) for c in combinations(range(12), 3))
    assert res_rand["chi_phi"] >= opt_rand - 1e-12

    # 3 cụm tách biệt rõ -> PAM phải đạt đúng nghiệm tối ưu toàn cục
    X_sep = np.vstack(
        [
            rng.normal(loc=0.0, scale=0.1, size=(4, 3)),
            rng.normal(loc=10.0, scale=0.1, size=(4, 3)),
            rng.normal(loc=-10.0, scale=0.1, size=(4, 3)),
        ]
    )
    D_sep = ma_tran_khoang_cach(X_sep)
    res_sep = pam(D_sep, k=3)
    opt_sep = min(chi_phi(D_sep, list(c)) for c in combinations(range(12), 3))
    assert np.isclose(res_sep["chi_phi"], opt_sep, atol=1e-10)


def test_pam_khop_thu_vien_kmedoids_1000_hat():
    kmedoids = pytest.importorskip("kmedoids")

    arff_path = ROOT_DIR / "data" / "raw" / "DryBeanDataset" / "Dry_Bean_Dataset.arff"
    _, X_df, y_s = doc_va_kiem_ke(arff_path)
    split = chuan_bi(X_df.to_numpy(dtype=np.float64), y_s.to_numpy(dtype=str), seed=20262027)
    idx_sub = lay_mau_con(split["y_tr"], n_mau=1000, seed=20262027)
    X_sub = split["Z_tr"][idx_sub]

    D = ma_tran_khoang_cach(X_sub, co_khoi=512)
    res_ours = pam(D, k=7)
    res_lib = kmedoids.pam(D, 7, max_iter=500, init="build")

    # Tổng chi phí bằng nhau ±1e-6
    assert abs(res_ours["chi_phi"] - float(res_lib.loss)) <= 1e-6

    # Trùng phân hoạch bất biến hoán vị >= 95% (kỳ vọng ~100%)
    trung = _ty_le_trung_hoan_vi(res_ours["nhan"], np.asarray(res_lib.labels))
    assert trung >= 0.95

    # gan_medoid khớp nhãn nội mẫu con (trừ các ca khoảng cách hòa tuyệt đối nếu có)
    nhan_gan = gan_medoid(X_sub, X_sub[res_ours["medoid"]])
    assert _ty_le_trung_hoan_vi(res_ours["nhan"], nhan_gan) >= 0.999

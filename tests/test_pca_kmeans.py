import sys
from pathlib import Path

import numpy as np
import pytest
from scipy.optimize import linear_sum_assignment
from sklearn.cluster import KMeans as SklearnKMeans
from sklearn.datasets import make_blobs
from sklearn.decomposition import PCA as SklearnPCA
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from data.nap import doc_va_kiem_ke
from data.tien_xu_ly import chuan_bi, lay_mau_con
from experiments.chay import ari, bang_cheo, nmi
from models.kmeans import kmeans, kmeanspp
from models.pca import chieu, dung_nguoc, khop_pca, k_giu, phuong_sai_tich_luy


def _ty_le_trung_hoan_vi(y_a: np.ndarray, y_b: np.ndarray) -> float:
    """Tính tỷ lệ trùng nhãn tối ưu bất biến hoán vị qua linear_sum_assignment."""
    ua, ia = np.unique(y_a, return_inverse=True)
    ub, ib = np.unique(y_b, return_inverse=True)
    m = max(len(ua), len(ub))
    cost = np.zeros((m, m), dtype=np.int64)
    np.add.at(cost, (ia, ib), 1)
    r_ind, c_ind = linear_sum_assignment(-cost)
    return float(cost[r_ind, c_ind].sum()) / float(len(y_a))


@pytest.fixture(scope="module")
def dry_bean_split():
    arff_path = ROOT_DIR / "data" / "raw" / "DryBeanDataset" / "Dry_Bean_Dataset.arff"
    _, X_df, y_s = doc_va_kiem_ke(arff_path)
    X = X_df.to_numpy(dtype=np.float64)
    y = y_s.to_numpy(dtype=str)
    return X, y, chuan_bi(X, y, seed=20262027, chuan_hoa=True)


def test_pca_khop_sklearn_va_dung_nguoc(dry_bean_split):
    _, _, split = dry_bean_split
    Z_tr, Z_te = split["Z_tr"], split["Z_te"]

    mh = khop_pca(Z_tr)
    sk = SklearnPCA(n_components=16).fit(Z_tr)

    # So từng trục bằng |Vt_minh[i] @ Vt_sk[i]| ≈ 1
    for i in range(16):
        dot = abs(float(mh["Vt"][i] @ sk.components_[i]))
        assert np.isclose(dot, 1.0, atol=1e-8)

    assert np.allclose(mh["phuong_sai"], sk.explained_variance_, atol=1e-8)
    assert np.allclose(mh["ty_le"], sk.explained_variance_ratio_, atol=1e-8)
    assert np.isclose(float(np.sum(mh["ty_le"])), 1.0, atol=1e-12)

    # Chiếu trùng sk.transform (sai khác tối đa ở dấu từng trục)
    P_minh = chieu(mh, Z_te, 16)
    P_sk = sk.transform(Z_te)
    assert np.allclose(np.abs(P_minh), np.abs(P_sk), atol=1e-7)

    # Cột sau chiếu không tương quan (ma trận hiệp phương sai ≈ đường chéo)
    P_tr = chieu(mh, Z_tr, 16)
    cov = np.cov(P_tr, rowvar=False)
    off_diag = cov - np.diag(np.diag(cov))
    assert np.allclose(off_diag, 0.0, atol=1e-8)

    # d=16 dựng ngược chính xác, và lỗi dựng ngược giảm đơn điệu theo d
    Z_rec_16 = dung_nguoc(mh, P_minh, 16)
    assert np.allclose(Z_rec_16, Z_te, atol=1e-8)

    mse_list = [
        float(np.mean((Z_te - dung_nguoc(mh, chieu(mh, Z_te, d), d)) ** 2))
        for d in range(1, 17)
    ]
    assert np.all(np.diff(mse_list) <= 1e-12)

    # Sanity k_giu cho các mốc 80%, 90%, 95%, 99%
    tich_luy = phuong_sai_tich_luy(mh)
    assert len(tich_luy) == 16
    assert k_giu(mh, 0.80) == 2
    assert k_giu(mh, 0.90) == 4
    assert k_giu(mh, 0.95) == 4
    assert k_giu(mh, 0.99) == 7


def test_kmeans_khop_sklearn_cung_init(dry_bean_split):
    _, _, split = dry_bean_split
    Z_tr, y_tr = split["Z_tr"], split["y_tr"]
    idx_sub = lay_mau_con(y_tr, n_mau=1500, seed=7)
    X_sub = Z_tr[idx_sub]

    rng = np.random.default_rng(123)
    init_idx = rng.choice(len(X_sub), size=7, replace=False)
    tam_0 = X_sub[init_idx].copy()

    res_minh = kmeans(X_sub, k=7, max_iter=300, tol=1e-4, init=tam_0)
    sk = SklearnKMeans(n_clusters=7, init=tam_0, n_init=1, max_iter=300, tol=1e-4, algorithm="lloyd").fit(X_sub)

    trung = _ty_le_trung_hoan_vi(res_minh["nhan"], sk.labels_)
    assert trung >= 0.99
    assert np.all(np.diff(res_minh["lich_su_sse"]) <= 1e-10)


def test_kmeans_tinh_chat_co_ban_va_cum_rong():
    # 3 đám cầu tách biệt rõ -> ARI = 1
    X_blob, y_blob = make_blobs(n_samples=180, centers=3, cluster_std=0.35, random_state=42)
    res_blob = kmeans(X_blob, k=3, n_init=5, seed=42)
    assert np.isclose(ari(y_blob, res_blob["nhan"]), 1.0, atol=1e-12)

    # k=1 -> tâm = trung bình
    res_k1 = kmeans(X_blob, k=1, n_init=1, seed=0)
    assert np.allclose(res_k1["tam"][0], X_blob.mean(axis=0), atol=1e-10)

    # Tái lập theo seed
    res_a = kmeans(X_blob, k=3, n_init=5, seed=99)
    res_b = kmeans(X_blob, k=3, n_init=5, seed=99)
    assert np.array_equal(res_a["nhan"], res_b["nhan"])

    # Cụm rỗng khi khởi tạo tâm ở rất xa không sinh NaN
    init_rong = np.vstack([X_blob[:2], np.array([[1000.0, 1000.0]])])
    res_rong = kmeans(X_blob, k=3, init=init_rong)
    assert not np.isnan(res_rong["tam"]).any()
    assert not np.isnan(res_rong["sse"])


def test_kmeanspp_phan_phoi_xac_suat_d2():
    X = np.array([[0.0, 0.0], [1.0, 0.0], [0.0, 4.0], [8.0, 0.0]])
    n = len(X)
    # Tính xác suất lý thuyết điểm được chọn làm tâm thứ 2 sau khi tâm đầu chọn đều
    p_ly_thuyet = np.zeros(n, dtype=np.float64)
    for i in range(n):
        d2 = np.sum((X - X[i]) ** 2, axis=1)
        p_ly_thuyet += (1.0 / n) * (d2 / d2.sum())

    rng = np.random.default_rng(2026)
    dem = np.zeros(n, dtype=np.int64)
    n_runs = 20000
    for _ in range(n_runs):
        tam = kmeanspp(X, k=2, rng=rng)
        # Tìm chỉ số khớp tâm thứ 2
        idx2 = int(np.argmin(np.sum((X - tam[1]) ** 2, axis=1)))
        dem[idx2] += 1

    p_thuc_nghiem = dem / n_runs
    assert np.all(np.abs(p_thuc_nghiem - p_ly_thuyet) <= 0.02)


def test_kmeans_chuan_hoa_vuot_troi_chua_chuan_hoa(dry_bean_split):
    _, _, split = dry_bean_split
    Z_tr, X_tr, y_tr = split["Z_tr"], split["X_tr"], split["y_tr"]
    idx_sub = lay_mau_con(y_tr, n_mau=3000, seed=20262027)

    res_std = kmeans(Z_tr[idx_sub], k=7, n_init=10, seed=20262027)
    res_raw = kmeans(X_tr[idx_sub], k=7, n_init=10, seed=20262027)

    ari_std = ari(y_tr[idx_sub], res_std["nhan"])
    ari_raw = ari(y_tr[idx_sub], res_raw["nhan"])
    assert ari_std > ari_raw + 0.15


def test_ari_nmi_bang_cheo_khop_sklearn(dry_bean_split):
    _, _, split = dry_bean_split
    y_tr = split["y_tr"]
    rng = np.random.default_rng(55)

    # Bất biến hoán vị & khớp sklearn
    nhan = rng.integers(0, 7, size=len(y_tr))
    perm = rng.permutation(7)
    nhan_perm = perm[nhan]

    ari_minh = ari(y_tr, nhan)
    ari_sk = adjusted_rand_score(y_tr, nhan)
    assert np.isclose(ari_minh, ari_sk, atol=1e-10)
    assert np.isclose(ari_minh, ari(y_tr, nhan_perm), atol=1e-12)
    assert abs(ari_minh) < 0.01  # nhãn ngẫu nhiên ≈ 0 ± 0.01

    nmi_minh = nmi(y_tr, nhan)
    nmi_sk = normalized_mutual_info_score(y_tr, nhan, average_method="arithmetic")
    assert np.isclose(nmi_minh, nmi_sk, atol=1e-10)

    # Biên: 1 cụm = 0, đồng nhất = 1
    assert ari(y_tr, np.zeros(len(y_tr), dtype=int)) == 0.0
    assert ari(y_tr, y_tr) == 1.0

    # Bảng chéo có tổng = n, cộng đúng từng hàng và cột
    bc = bang_cheo(y_tr, nhan)
    assert int(bc.values.sum()) == len(y_tr)
    for cls in bc.index:
        assert int(bc.loc[cls].sum()) == int(np.sum(y_tr == cls))
    for c_idx in range(7):
        assert int(bc[f"Cum_{c_idx}"].sum()) == int(np.sum(nhan == c_idx))

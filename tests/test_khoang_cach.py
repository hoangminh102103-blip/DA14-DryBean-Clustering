import sys
from pathlib import Path

import numpy as np
import pytest
from scipy.spatial.distance import cdist
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from data.nap import doc_va_kiem_ke
from models.khoang_cach import (
    euclid_theo_khoi,
    gan_gan_nhat,
    ma_tran_khoang_cach,
    silhouette_nhieu_phan_hoach,
    silhouette_theo_khoi,
)


def test_ma_tran_khoang_cach_khop_cdist_ngau_nhien():
    rng = np.random.default_rng(123)
    X = rng.normal(size=(300, 16))
    D = ma_tran_khoang_cach(X, co_khoi=64)
    D_ref = cdist(X, X, metric="euclidean")

    assert D.dtype == np.float64
    assert np.allclose(D, D_ref, atol=1e-8, rtol=1e-12)
    assert np.array_equal(D, D.T)
    assert np.all(np.diag(D) == 0.0)


def test_ma_tran_khoang_cach_500_hat_that():
    arff_path = ROOT_DIR / "data" / "raw" / "DryBeanDataset" / "Dry_Bean_Dataset.arff"
    _, X_df, _ = doc_va_kiem_ke(arff_path)
    rng = np.random.default_rng(20262027)
    idx = rng.choice(len(X_df), size=500, replace=False)
    X_raw = X_df.iloc[idx].to_numpy(dtype=np.float64)
    X_std = StandardScaler().fit_transform(X_raw)

    for X_sub in (X_std, X_raw):
        D = ma_tran_khoang_cach(X_sub, co_khoi=128)
        D_ref = cdist(X_sub, X_sub, metric="euclidean")
        assert np.allclose(D, D_ref, atol=1e-8, rtol=1e-12)
        assert np.all(np.diag(D) == 0.0)


@pytest.mark.parametrize("co_khoi", [1, 7, 128, 150])
def test_doc_lap_voi_kich_thuoc_khoi_va_bat_dang_thuc_tam_giac(co_khoi):
    rng = np.random.default_rng(99)
    X = rng.normal(size=(150, 8))
    D = ma_tran_khoang_cach(X, co_khoi=co_khoi)
    D_ref = cdist(X, X, metric="euclidean")
    assert np.allclose(D, D_ref, atol=1e-10)

    # Kiểm tra bất đẳng thức tam giác trên các bộ ba điểm ngẫu nhiên
    triples = rng.integers(0, len(X), size=(500, 3))
    i, j, k = triples[:, 0], triples[:, 1], triples[:, 2]
    assert np.all(D[i, k] <= D[i, j] + D[j, k] + 1e-12)


def test_gan_gan_nhat_khop_cdist():
    rng = np.random.default_rng(7)
    X = rng.normal(size=(215, 6))
    tam = rng.normal(size=(5, 6))

    nhan, d_min = gan_gan_nhat(X, tam, co_khoi=32)
    D_ref = cdist(X, tam, metric="euclidean")
    assert np.array_equal(nhan, np.argmin(D_ref, axis=1))
    assert np.allclose(d_min, np.min(D_ref, axis=1), atol=1e-10)


def test_silhouette_theo_khoi_khop_sklearn_va_cum_1_diem():
    rng = np.random.default_rng(42)
    X = np.vstack([
        rng.normal(loc=0.0, scale=0.4, size=(35, 5)),
        rng.normal(loc=4.0, scale=0.4, size=(35, 5)),
        np.array([[10.0, 10.0, 10.0, 10.0, 10.0]]),  # cụm 1 điểm
    ])
    nhan = np.array([0] * 35 + [1] * 35 + [2])

    s_i, s_tb = silhouette_theo_khoi(X, nhan, co_khoi=16)
    s_ref = silhouette_score(X, nhan, metric="euclidean")

    assert s_i[-1] == 0.0
    assert np.isclose(s_tb, s_ref, atol=1e-9)

    # Trường hợp 1 cụm duy nhất -> 0.0
    _, s_single = silhouette_theo_khoi(X, np.zeros(len(X), dtype=int), co_khoi=32)
    assert s_single == 0.0

    # Đánh giá gộp nhiều phân hoạch trong 1 lượt phải khớp từng gọi riêng lẻ
    ds_nhan = [
        nhan,
        rng.integers(0, 4, size=len(X)),
        np.zeros(len(X), dtype=int),
    ]
    batch_s = silhouette_nhieu_phan_hoach(X, ds_nhan, co_khoi=16)
    for s_b, nh in zip(batch_s, ds_nhan):
        assert np.isclose(s_b, silhouette_theo_khoi(X, nh, co_khoi=16)[1], atol=1e-12)


def test_sanity_bo_nho_13611():
    gb = (13611 ** 2 * 8) / 1e9
    assert np.isclose(gb, 1.48, atol=0.01)

import sys
from pathlib import Path

import numpy as np
from scipy.spatial.distance import mahalanobis as scipy_mahalanobis
from sklearn.preprocessing import StandardScaler

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from data.nap import doc_va_kiem_ke
from models.khoang_cach import ma_tran_khoang_cach
from models.mahalanobis import (
    do_so_dieu_kien_pca,
    ma_tran_mahalanobis,
    nghich_dao_gia_svd,
    phan_ra_mahalanobis,
)


def test_mahalanobis_khop_scipy_va_tuong_duong_lam_trang():
    rng = np.random.default_rng(2026)
    X = rng.normal(size=(80, 5))
    # Làm cho các cột tương quan thực sự để ma trận hiệp phương sai không đơn vị
    X[:, 2] = 0.8 * X[:, 0] + 0.3 * X[:, 1] + 0.1 * X[:, 2]

    cov = np.cov(X, rowvar=False)
    S_inv, W, _ = nghich_dao_gia_svd(cov, nguong_cat=1e-12, tikonov=0.0)
    S_inv_ref = np.linalg.inv(cov)
    assert np.allclose(S_inv, S_inv_ref, atol=1e-8)

    D_mahal = ma_tran_mahalanobis(X, W, co_khoi=32, la_ma_tran_nghich_dao=False)
    D_from_sinv = ma_tran_mahalanobis(X, S_inv, co_khoi=32, la_ma_tran_nghich_dao=True)
    D_euclid_white = ma_tran_khoang_cach(X @ W.T, co_khoi=32)

    assert np.allclose(D_mahal, D_from_sinv, atol=1e-9)
    assert np.allclose(D_mahal, D_euclid_white, atol=1e-10)

    # Đối chiếu trực tiếp từng cặp với scipy.spatial.distance.mahalanobis
    for i, j in [(0, 1), (5, 20), (12, 79)]:
        d_scipy = scipy_mahalanobis(X[i], X[j], S_inv_ref)
        assert np.isclose(D_mahal[i, j], d_scipy, atol=1e-8)


def test_so_dieu_kien_pca_va_nghich_dao_gia_tren_dry_bean():
    arff_path = ROOT_DIR / "data" / "raw" / "DryBeanDataset" / "Dry_Bean_Dataset.arff"
    _, X_df, _ = doc_va_kiem_ke(arff_path)
    Z = StandardScaler().fit_transform(X_df.to_numpy(dtype=np.float64))

    df_cond = do_so_dieu_kien_pca(Z)
    assert len(df_cond) == 16
    # Số điều kiện tăng khi giữ lại các thành phần cuối đa cộng tuyến
    assert float(df_cond.iloc[3]["cond_Cov_d"]) < 50.0
    assert float(df_cond.iloc[15]["cond_Cov_d"]) > 1e6

    mh = phan_ra_mahalanobis(Z, nguong_cat=1e-3, tikonov=0.0)
    assert mh["so_chieu_giu"] < 16
    assert np.allclose(mh["W"].T @ mh["W"], mh["S_inv"], atol=1e-9)

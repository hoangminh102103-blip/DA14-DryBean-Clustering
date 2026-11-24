import sys
from pathlib import Path

import numpy as np
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from data.nap import doc_va_kiem_ke
from data.tien_xu_ly import (
    ap_chuan_hoa,
    chia_phan_tang,
    chuan_bi,
    khop_chuan_hoa,
    lay_mau_con,
    ma_hoa_nhan,
    tiem_ngoai_lai,
)


@pytest.fixture(scope="module")
def dry_bean_data():
    arff_path = ROOT_DIR / "data" / "raw" / "DryBeanDataset" / "Dry_Bean_Dataset.arff"
    _, X, y = doc_va_kiem_ke(arff_path)
    return X.to_numpy(dtype=np.float64), y.to_numpy(dtype=str)


def test_chia_phan_tang_khong_ro_ri_va_ty_le_lop(dry_bean_data):
    X, y = dry_bean_data
    res = chuan_bi(X, y, seed=20262027, chuan_hoa=True)
    X_tr, X_te = res["X_tr"], res["X_te"]
    y_tr, y_te = res["y_tr"], res["y_te"]
    idx_tr, idx_te = res["idx_tr"], res["idx_te"]
    scaler = res["scaler"]
    Z_tr = res["Z_tr"]

    # 10.888 + 2.723 = 13.611, tập hợp bao phủ toàn bộ và không giao nhau
    assert len(X_tr) == 10888
    assert len(X_te) == 2723
    assert len(X_tr) + len(X_te) == len(X) == 13611
    assert len(np.intersect1d(idx_tr, idx_te)) == 0
    assert np.array_equal(np.sort(np.concatenate([idx_tr, idx_te])), np.arange(len(X)))

    # Tỷ lệ lớp train/test lệch tỷ lệ gốc < 0.2%
    classes, counts_all = np.unique(y, return_counts=True)
    prop_all = counts_all / len(y)
    for cls, p_orig in zip(classes, prop_all):
        p_tr = np.mean(y_tr == cls)
        p_te = np.mean(y_te == cls)
        assert abs(p_tr - p_orig) < 0.002
        assert abs(p_te - p_orig) < 0.002

    # scaler.mean_ trùng X_tr.mean(0) và khác X.mean(0) toàn bộ
    assert np.allclose(scaler.mean_, X_tr.mean(axis=0), atol=1e-12)
    assert not np.allclose(scaler.mean_, X.mean(axis=0))

    # Sanity: Z_tr mean ≈ 0, std ≈ 1
    assert np.allclose(Z_tr.mean(axis=0), 0.0, atol=1e-12)
    assert np.allclose(Z_tr.std(axis=0, ddof=0), 1.0, atol=1e-12)


def test_chong_ro_ri_khi_bien_doi_tap_test(dry_bean_data):
    X, y = dry_bean_data
    X_tr, X_te, y_tr, y_te, _, _ = chia_phan_tang(X, y, ty_le_test=0.2, seed=20262027)
    scaler_goc = khop_chuan_hoa(X_tr)

    # Nhân toàn bộ X_te lên 1000 lần rồi kiểm chứng scaler khớp trên train không hề đổi
    X_mod = X.copy()
    _, _, _, _, idx_tr, idx_te = chia_phan_tang(X, y, ty_le_test=0.2, seed=20262027)
    X_mod[idx_te] = X_mod[idx_te] * 1000.0
    res_mod = chuan_bi(X_mod, y, seed=20262027, chuan_hoa=True)

    assert np.array_equal(scaler_goc.mean_, res_mod["scaler"].mean_)
    assert np.array_equal(scaler_goc.scale_, res_mod["scaler"].scale_)
    assert np.allclose(ap_chuan_hoa(scaler_goc, X_tr), res_mod["Z_tr"], atol=1e-12)

    # Baseline không chuẩn hóa
    res_raw = chuan_bi(X, y, seed=20262027, chuan_hoa=False)
    assert res_raw["scaler"] is None
    assert np.array_equal(res_raw["Z_tr"], res_raw["X_tr"])
    assert np.array_equal(res_raw["Z_te"], res_raw["X_te"])


def test_lay_mau_con_phan_tang(dry_bean_data):
    X, y = dry_bean_data
    _, _, y_tr, _, _, _ = chia_phan_tang(X, y, ty_le_test=0.2, seed=20262027)

    idx_1 = lay_mau_con(y_tr, n_mau=3000, seed=101)
    idx_1_repeat = lay_mau_con(y_tr, n_mau=3000, seed=101)
    idx_2 = lay_mau_con(y_tr, n_mau=3000, seed=102)

    assert len(idx_1) == 3000
    assert len(np.unique(idx_1)) == 3000
    assert np.array_equal(idx_1, idx_1_repeat)
    assert not np.array_equal(idx_1, idx_2)

    classes, counts_tr = np.unique(y_tr, return_counts=True)
    y_sub = y_tr[idx_1]
    for cls, c_tr in zip(classes, counts_tr):
        expected = 3000.0 * (c_tr / len(y_tr))
        actual = float(np.sum(y_sub == cls))
        assert abs(actual - expected) <= 1.0


def test_tiem_ngoai_lai_khong_sua_tai_cho(dry_bean_data):
    X, y = dry_bean_data
    X_tr, _, _, _, _, _ = chia_phan_tang(X, y, ty_le_test=0.2, seed=20262027)
    X_tr_backup = X_tr.copy()

    X_out, info = tiem_ngoai_lai(X_tr, ty_le=0.01, he_so=(8, 12), cot="Area", seed=42)
    X_out_repeat, info_repeat = tiem_ngoai_lai(X_tr, ty_le=0.01, he_so=(8, 12), cot="Area", seed=42)

    # Đầu vào không bị sửa
    assert np.array_equal(X_tr, X_tr_backup)

    # Tái lập theo seed
    assert np.array_equal(info["idx"], info_repeat["idx"])
    assert np.allclose(info["he_so"], info_repeat["he_so"])
    assert np.array_equal(X_out, X_out_repeat)

    n = len(X_tr)
    expected_count = int(round(0.01 * n))
    idx = info["idx"]
    assert len(idx) == expected_count

    # Các hàng không bị tiêm giữ nguyên, các cột khác không bị đổi
    mask_clean = np.ones(n, dtype=bool)
    mask_clean[idx] = False
    assert np.array_equal(X_out[mask_clean], X_tr[mask_clean])
    assert np.array_equal(X_out[:, 1:], X_tr[:, 1:])

    ratios = X_out[idx, 0] / X_tr[idx, 0]
    assert np.all((ratios >= 8.0) & (ratios <= 12.0))


def test_ma_hoa_nhan(dry_bean_data):
    _, y = dry_bean_data
    y_int, ten_lop = ma_hoa_nhan(y)
    assert len(ten_lop) == 7
    assert y_int.min() == 0 and y_int.max() == 6
    for i, name in enumerate(ten_lop):
        assert np.all(y[y_int == i] == name)

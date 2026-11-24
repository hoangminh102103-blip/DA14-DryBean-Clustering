import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from data.nap import doc_va_kiem_ke
from data.tien_xu_ly import chia_phan_tang, tiem_ngoai_lai
from experiments.chay import (
    _chuan_bi_khong_gian,
    chay_mot,
    kiem_dinh_wilcoxon,
    phan_lop_moc_tren,
    quet,
    tong_hop,
    xuat_benchmark_table,
)


def test_hai_thuat_toan_dung_cung_ngoai_lai_va_schema_web():
    arff_path = ROOT_DIR / "data" / "raw" / "DryBeanDataset" / "Dry_Bean_Dataset.arff"
    _, X_df, y_s = doc_va_kiem_ke(arff_path)
    X_all = X_df.to_numpy(dtype=np.float64)
    y_all = y_s.to_numpy(dtype=str)

    X_tr, _, y_tr, _, _, _ = chia_phan_tang(X_all, y_all, ty_le_test=0.2, seed=20262027)

    # Cùng một seed -> băm SHA-256 của idx và he_so ngoại lai dùng cho hai thuật toán bằng nhau tuyệt đối
    _, info_a = tiem_ngoai_lai(X_tr, ty_le=0.01, he_so=(8, 12), cot="Area", seed=20262027)
    _, info_b = tiem_ngoai_lai(X_tr, ty_le=0.01, he_so=(8, 12), cot="Area", seed=20262027)
    hash_a = hashlib.sha256(info_a["idx"].tobytes() + info_a["he_so"].tobytes()).hexdigest()
    hash_b = hashlib.sha256(info_b["idx"].tobytes() + info_b["he_so"].tobytes()).hexdigest()
    assert hash_a == hash_b

    # Quét nhỏ để kiểm tra cấu trúc DataFrame, schema JSON web và p-value
    df_nho = quet(
        X_tr,
        y_tr,
        luoi_d=[2, 4, 16],
        luoi_kc=[2, 7],
        seeds=[20262027, 20262028],
        ngoai_lai=(False, True),
        n_mau=400,
        chay_baseline=True,
        thu_muc_checkpoint=None,
        workers=1,
    )
    cot_bat_buoc = {
        "dieu_kien",
        "thuat_toan",
        "d",
        "kc",
        "seed",
        "ari",
        "nmi",
        "sil",
        "thoi_gian_s",
        "chi_phi",
    }
    assert cot_bat_buoc.issubset(df_nho.columns)

    # Baseline k-means chưa chuẩn hóa phải kém hơn k-means chuẩn hóa
    ari_raw = float(
        df_nho[(df_nho["dieu_kien"] == "sach") & (df_nho["thuat_toan"] == "kmeans_chua_chuan_hoa")]["ari"].mean()
    )
    ari_std = float(
        df_nho[
            (df_nho["dieu_kien"] == "sach")
            & (df_nho["thuat_toan"] == "kmeans")
            & (df_nho["d"] == 16)
            & (df_nho["kc"] == 7)
        ]["ari"].mean()
    )
    assert ari_raw < ari_std

    # Baseline 1 cụm cho ARI = 0
    ari_1c = float(df_nho[df_nho["thuat_toan"] == "mot_cum"]["ari"].max())
    assert ari_1c == 0.0

    _, _, bang_ts = tong_hop(df_nho)
    bt = xuat_benchmark_table(bang_ts)
    assert set(bt.keys()) == {"2", "4", "16"}
    for d_key in ("2", "4", "16"):
        assert len(bt[d_key]) == 2
        row = bt[d_key][0]
        assert {"k", "cMed", "cKm", "cSil", "cSilKm", "cTime", "oMed", "oKm", "oSil", "oTime", "dMed", "dKm"}.issubset(
            row.keys()
        )

    df_w = kiem_dinh_wilcoxon(df_nho, cac_d=(2, 4, 16), kc=7)
    assert len(df_w) > 0
    assert np.all((df_w["p_value"] >= 0.0) & (df_w["p_value"] <= 1.0))


def test_phan_lop_moc_tren_khong_ro_ri():
    arff_path = ROOT_DIR / "data" / "raw" / "DryBeanDataset" / "Dry_Bean_Dataset.arff"
    _, X_df, y_s = doc_va_kiem_ke(arff_path)
    df_rf, cm_rf, _ = phan_lop_moc_tren(
        X_df.to_numpy(dtype=np.float64), y_s.to_numpy(dtype=str), seed=20262027
    )
    assert len(df_rf) == 5
    assert "Dummy_LopPhoBienNhat" in set(df_rf["cau_hinh"])
    acc_dummy = float(df_rf.loc[df_rf["cau_hinh"] == "Dummy_LopPhoBienNhat", "test_accuracy"].iloc[0])
    acc_rf = float(df_rf.loc[df_rf["cau_hinh"] == "RF_16D_StandardScaler", "test_accuracy"].iloc[0])
    assert 0.25 < acc_dummy < 0.27
    assert acc_rf > 0.88
    assert int(cm_rf.values.sum()) == 2723

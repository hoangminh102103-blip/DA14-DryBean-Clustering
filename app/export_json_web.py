import json
import shutil
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from data.nap import doc_va_kiem_ke
from data.tien_xu_ly import ap_chuan_hoa, khop_chuan_hoa
from models.pca import chieu, khop_pca


def xuat_du_lieu_web():
    duong_dan_arff = ROOT_DIR / "data" / "raw" / "DryBeanDataset" / "Dry_Bean_Dataset.arff"
    df, X, y = doc_va_kiem_ke(duong_dan_arff)

    # Tái sử dụng đúng bộ chuẩn hóa và PCA-SVD tự viết của dự án (quy ước 07b)
    scaler = khop_chuan_hoa(X)
    X_scaled = ap_chuan_hoa(scaler, X)

    pca_mh = khop_pca(X_scaled)
    X_pca = chieu(pca_mh, X_scaled, 16)

    feature_cols = list(X.columns)
    beans_payload = [
        {
            "id": idx,
            "variety": str(y.iloc[idx]),
            "varietyLabel": str(y.iloc[idx]).capitalize(),
            "features": {col: round(float(X.iloc[idx][col]), 6) for col in feature_cols},
            "stdFeatures": [round(float(v), 5) for v in X_scaled[idx]],
            "pc": [round(float(v), 5) for v in X_pca[idx]],
        }
        for idx in range(len(df))
    ]

    payload = {
        "beans": beans_payload,
        "pcaModel": {
            "mean": [round(float(v), 6) for v in scaler.mean_],
            "std": [round(float(v), 6) for v in scaler.scale_],
            "components": [[round(float(c), 6) for c in row] for row in pca_mh["Vt"]],
            "explainedVarianceRatio": [round(float(v), 6) for v in pca_mh["ty_le"]],
        },
    }

    # Gộp bảng thực nghiệm Bước 7 (k = 2..16, d = "2", "4", "16") nếu đã chạy xong experiments/chay.py
    file_benchmark = ROOT_DIR / "results" / "bang" / "benchmark_results.json"
    if file_benchmark.exists():
        with open(file_benchmark, "r", encoding="utf-8") as f:
            payload["benchmarkTable"] = json.load(f)
        print("[+] Đã gộp kết quả thực nghiệm thật từ results/bang/benchmark_results.json.")

    duong_dan_xuat = ROOT_DIR / "results" / "da14_web_data.json"
    duong_dan_xuat.parent.mkdir(parents=True, exist_ok=True)
    json_str = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    duong_dan_xuat.write_text(json_str, encoding="utf-8")
    print(f"[OK] Đã xuất JSON tại: {duong_dan_xuat}")

    # Đồng bộ sang thư mục web (cả JSON lẫn JS preload để mở trực tiếp file:// index.html không bị CORS)
    for ten_thu_muc in ("dry_bean_web", "da14_dry_bean_web"):
        thu_muc_web = ROOT_DIR / ten_thu_muc
        if thu_muc_web.exists():
            shutil.copy2(duong_dan_xuat, thu_muc_web / "da14_web_data.json")
            js_bundle = thu_muc_web / "js" / "da14_web_data.js"
            js_bundle.parent.mkdir(parents=True, exist_ok=True)
            js_bundle.write_text(f"window.DA14_PRELOADED_DATA = {json_str};\n", encoding="utf-8")
            print(f"[OK] Đã đồng bộ JSON + JS preload sang: {thu_muc_web}")


if __name__ == "__main__":
    xuat_du_lieu_web()

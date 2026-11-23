import json
import shutil
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from data.nap import doc_va_kiem_ke


def xuat_du_lieu_web():
    duong_dan_arff = ROOT_DIR / "data" / "raw" / "DryBeanDataset" / "Dry_Bean_Dataset.arff"
    df, X, y = doc_va_kiem_ke(duong_dan_arff)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    pca = PCA(n_components=16)
    X_pca = pca.fit_transform(X_scaled)

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
            "components": [[round(float(c), 6) for c in row] for row in pca.components_],
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
    with open(duong_dan_xuat, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
    print(f"[OK] Đã xuất JSON tại: {duong_dan_xuat}")

    # Tự động chép sang thư mục web nếu đặt cùng thư mục gốc
    thu_muc_web = ROOT_DIR / "da14_dry_bean_web"
    if thu_muc_web.exists():
        shutil.copy2(duong_dan_xuat, thu_muc_web / "da14_web_data.json")
        print(f"[OK] Đã đồng bộ sang: {thu_muc_web / 'da14_web_data.json'}")


if __name__ == "__main__":
    xuat_du_lieu_web()
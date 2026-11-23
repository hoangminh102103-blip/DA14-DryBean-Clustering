import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.io.arff import loadarff
from sklearn.preprocessing import StandardScaler

ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_ARFF_PATH = ROOT_DIR / "data" / "raw" / "DryBeanDataset" / "Dry_Bean_Dataset.arff"
DEFAULT_REPORT_PATH = ROOT_DIR / "bao_cao" / "Bao_Cao_DA14_DryBean_Buoc1.md"
UCI_DRY_BEAN_ZIP_URL = "https://archive.ics.uci.edu/static/public/602/dry+bean+dataset.zip"

def tai_neu_thieu(duong_dan_arff: Path = DEFAULT_ARFF_PATH) -> Path:
    """Tự động tải và giải nén bộ Dry Bean (UCI ID 602) nếu máy chưa có."""
    duong_dan_arff = Path(duong_dan_arff)
    if duong_dan_arff.exists():
        return duong_dan_arff

    thu_muc_dich = duong_dan_arff.parent
    thu_muc_dich.mkdir(parents=True, exist_ok=True)
    file_zip_tam = thu_muc_dich / "dry_bean_dataset.zip"

    print(f"[!] Không tìm thấy dữ liệu tại {duong_dan_arff}. Đang tải từ UCI...")
    try:
        req = urllib.request.Request(UCI_DRY_BEAN_ZIP_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp, open(file_zip_tam, "wb") as out:
            out.write(resp.read())

        with zipfile.ZipFile(file_zip_tam, "r") as zf:
            for member in zf.infolist():
                if member.is_dir():
                    continue
                ten_file = Path(member.filename).name
                if ten_file:
                    (thu_muc_dich / ten_file).write_bytes(zf.read(member.filename))

        file_zip_tam.unlink(missing_ok=True)
        if not duong_dan_arff.exists():
            raise FileNotFoundError("Giải nén xong nhưng không thấy Dry_Bean_Dataset.arff")
        print(f"[OK] Đã tải và giải nén dữ liệu vào: {thu_muc_dich}")
        return duong_dan_arff

    except Exception as err:
        file_zip_tam.unlink(missing_ok=True)
        raise FileNotFoundError(
            f"Không thể tự động tải dữ liệu ({err}).\n"
            "Vui lòng tải thủ công tại: https://archive.ics.uci.edu/dataset/602/dry+bean+dataset\n"
            f"và giải nén tệp Dry_Bean_Dataset.arff vào thư mục: {thu_muc_dich}"
        ) from err
    
def doc_va_kiem_ke(duong_dan: Path | str | None = None):
    duong_dan_thuc_te = tai_neu_thieu(Path(duong_dan) if duong_dan else DEFAULT_ARFF_PATH)

    data, _ = loadarff(duong_dan_thuc_te)
    df = pd.DataFrame(data)
    df["Class"] = df["Class"].str.decode("utf-8")

    # 1. Xác nhận cột Class nằm ở cuối
    assert df.columns[-1] == "Class", "Lỗi: Cột cuối cùng không phải là Class!"
    print("1. Xác nhận cột 'Class' nằm ở cuối cùng.")

    # 2. Tách riêng và kiểm tra 16 cột đặc trưng số
    X = df.iloc[:, :-1]
    y = df["Class"]
    assert len(X.select_dtypes(exclude="number").columns) == 0, "Lỗi: Có cột đặc trưng không phải số!"
    print(f"2. Đã tách {X.shape[1]} cột đặc trưng số và cột nhãn 'Class'.")

    # 3. Bảng Min và Max của 16 đặc trưng
    bang_min_max = pd.DataFrame({"Min": X.min(), "Max": X.max()})
    print("\n3. Bảng Min và Max của 16 cột đặc trưng:")
    print(bang_min_max)

    # 4 & 5. Gộp kích thước, kiểu từng cột và số ô khuyết thành 1 bảng gọn
    bang_cot = pd.DataFrame({
        "Kieu_du_lieu": df.dtypes,
        "So_o_khuyet": df.isna().sum(),
    })
    print(f"\n4 & 5. Kích thước: {df.shape[0]} dòng × {df.shape[1]} cột | Bảng kiểu dữ liệu & ô khuyết:")
    print(bang_cot)

    # 6. Số bản ghi trùng lặp hoàn toàn
    so_trung_lap = int(df.duplicated().sum())
    print(f"\n6. Số bản ghi trùng lặp hoàn toàn: {so_trung_lap}")

    # 7. Phân bố lớp
    print("\n7. Phân bố 7 giống đậu (Class):")
    print(df["Class"].value_counts())

    return df, X, y

def doi_chieu_va_ghi_bao_cao(df, X, y, duong_dan_bao_cao: Path | str = DEFAULT_REPORT_PATH):
    duong_dan_bao_cao = Path(duong_dan_bao_cao)

    # Đối chiếu kích thước chung
    de_tai_chung = {
        "Số dòng": 13611,
        "Số cột": 17,
        "Số cột đặc trưng": 16,
        "Số giống đậu (lớp)": 7,
    }
    thuc_te_chung = {
        "Số dòng": df.shape[0],
        "Số cột": df.shape[1],
        "Số cột đặc trưng": X.shape[1],
        "Số giống đậu (lớp)": y.nunique(),
    }
    bang_doi_chieu_chung = pd.DataFrame({"De_tai": pd.Series(de_tai_chung), "Thuc_te": pd.Series(thuc_te_chung)})
    bang_doi_chieu_chung["Chenh_lech"] = bang_doi_chieu_chung["Thuc_te"] - bang_doi_chieu_chung["De_tai"]

    # Đối chiếu phân bố 7 giống đậu
    de_tai_lop = {
        "DERMASON": 3546,
        "SIRA": 2636,
        "SEKER": 2027,
        "HOROZ": 1928,
        "CALI": 1630,
        "BARBUNYA": 1322,
        "BOMBAY": 522,
    }
    bang_doi_chieu_lop = pd.DataFrame({
        "De_tai": pd.Series(de_tai_lop),
        "Thuc_te": y.value_counts(),
    }).fillna(0).astype(int)
    bang_doi_chieu_lop["Chenh_lech"] = bang_doi_chieu_lop["Thuc_te"] - bang_doi_chieu_lop["De_tai"]

    # Tính các chỉ số bổ sung đề bài nêu để đối chiếu
    X_scaled = StandardScaler().fit_transform(X)
    cond_z = float(np.linalg.cond(X_scaled))
    cond_cov = float(np.linalg.cond(np.cov(X_scaled, rowvar=False)))

    corr_abs = X.corr().abs()
    upper = corr_abs.where(np.triu(np.ones(corr_abs.shape), k=1).astype(bool))
    so_cap_cao = int((upper > 0.9).sum().sum())
    tong_cap = X.shape[1] * (X.shape[1] - 1) // 2

    ty_le_lop_lon_nhat = y.value_counts().iloc[0] / len(df) * 100

    bang_chi_so_de_tai = pd.DataFrame([
        {"Chi_so": "Min toàn bảng đặc trưng", "De_tai": "0.000564", "Thuc_te": f"{X.min().min():.6f}"},
        {"Chi_so": "Max toàn bảng đặc trưng", "De_tai": "263261", "Thuc_te": f"{X.max().max():.0f}"},
        {"Chi_so": "Khoảng giá trị Area", "De_tai": "20420 – 254616", "Thuc_te": f"{X['Area'].min():.0f} – {X['Area'].max():.0f}"},
        {"Chi_so": "Tỷ lệ lớp lớn nhất (DERMASON)", "De_tai": "26.05%", "Thuc_te": f"{ty_le_lop_lon_nhat:.2f}%"},
        {"Chi_so": "Số cặp tương quan |r| > 0.9", "De_tai": "21 / 120", "Thuc_te": f"{so_cap_cao} / {tong_cap}"},
        {"Chi_so": "Số điều kiện cond(Z) sau StandardScaler", "De_tai": "~2230", "Thuc_te": f"{cond_z:.2f}"},
        {"Chi_so": "Số điều kiện ma trận hiệp phương sai cond(Cov)", "De_tai": "~4.97e+06 (2230²)", "Thuc_te": f"{cond_cov:.2e}"},
    ]).set_index("Chi_so")

    print("\n=== ĐỐI CHIẾU KÍCH THƯỚC & PHÂN BỐ LỚP ===")
    print(bang_doi_chieu_chung)
    print("\n=== ĐỐI CHIẾU PHÂN BỐ TỪNG GIỐNG ĐẬU ===")
    print(bang_doi_chieu_lop)
    print("\n=== ĐỐI CHIẾU CÁC CHỈ SỐ ĐẶC TRƯNG TRONG ĐỀ TÀI ===")
    print(bang_chi_so_de_tai)

    co_lech = (bang_doi_chieu_chung["Chenh_lech"] != 0).any() or (bang_doi_chieu_lop["Chenh_lech"] != 0).any()
    nhan_xet_doi_chieu = (
        "Số liệu thực tế **khớp hoàn toàn 100%** với toàn bộ thông số ghi trong đề tài."
        if not co_lech
        else "**Có sự chênh lệch** giữa dữ liệu tải về và thông số đề tài (xem cột `Chenh_lech`)."
    )

    bang_min_max = pd.DataFrame({"Min": X.min(), "Max": X.max()})
    bang_cot = pd.DataFrame({"Kieu_du_lieu": df.dtypes, "So_o_khuyet": df.isna().sum()})
    so_trung_lap = int(df.duplicated().sum())

    duong_dan_bao_cao.parent.mkdir(parents=True, exist_ok=True)
    with open(duong_dan_bao_cao, "w", encoding="utf-8") as f:
        f.write("# BÁO CÁO ĐỒ ÁN DA-14: BẢY GIỐNG ĐẬU KHÔ NHÌN TỪ BÓNG CỦA CHÚNG\n\n")
        f.write("## Bước 1: Nạp dữ liệu và kiểm kê trung thực\n\n")

        f.write("### 1.1. Kích thước, kiểu dữ liệu và số ô khuyết\n")
        f.write(f"- **Số dòng:** {df.shape[0]}\n")
        f.write(f"- **Số cột:** {df.shape[1]} (gồm {X.shape[1]} cột đặc trưng số và cột nhãn `Class` ở cuối)\n")
        f.write(f"- **Số bản ghi trùng lặp hoàn toàn:** {so_trung_lap} (giữ nguyên để bảo toàn tập gốc UCI)\n\n")
        f.write("```text\n" + bang_cot.to_string() + "\n```\n\n")

        f.write("### 1.2. Bảng giá trị Min và Max của 16 đặc trưng\n")
        f.write("```text\n" + bang_min_max.to_string() + "\n```\n\n")

        f.write("### 1.3. Đối chiếu số liệu với đề tài\n")
        f.write("```text\n" + bang_doi_chieu_chung.to_string() + "\n```\n\n")
        f.write("```text\n" + bang_doi_chieu_lop.to_string() + "\n```\n\n")
        f.write("```text\n" + bang_chi_so_de_tai.to_string() + "\n```\n\n")
        f.write(f"- **Kết luận đối chiếu:** {nhan_xet_doi_chieu}\n")
        f.write(
            "- **Lưu ý đa cộng tuyến & Mahalanobis:** Số điều kiện của ma trận chuẩn hóa $Z$ là "
            f"$\\text{{cond}}(Z) = {cond_z:.2f}$ ($\\sigma_{{\\max}}/\\sigma_{{\\min}}$), dẫn tới số điều kiện của "
            f"ma trận hiệp phương sai $\\Sigma_Z$ đạt $\\text{{cond}}(\\Sigma_Z) = {cond_cov:.2e}$ — cần cộng điều chuẩn "
            "Tikonov ($\\Sigma + \\lambda I$) khi nghịch đảo cho khoảng cách Mahalanobis.\n"
        )

    print(f"\nĐã lưu báo cáo kiểm kê Bước 1 tại: {duong_dan_bao_cao}")

if __name__ == "__main__":
    df, X, y = doc_va_kiem_ke()
    doi_chieu_va_ghi_bao_cao(df, X, y)
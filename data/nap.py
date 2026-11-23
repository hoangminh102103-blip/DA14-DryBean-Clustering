import pandas as pd
from pathlib import Path
from scipy.io.arff import loadarff


def doc_va_kiem_ke(duong_dan):
    data, _ = loadarff(duong_dan)
    df = pd.DataFrame(data)
    df["Class"] = df["Class"].str.decode("utf-8")

    # 1. Xác nhận cột Class nằm ở cuối
    assert df.columns[-1] == "Class", "Lỗi: Cột cuối cùng không phải là Class!"
    print("1. Xác nhận cột 'Class' nằm ở cuối cùng")

    # 2. Tách riêng và kiểm tra các cột đặc trưng
    X = df.iloc[:, :-1]
    y = df["Class"]
    assert len(X.select_dtypes(exclude="number").columns) == 0, "Lỗi: Có cột đặc trưng không phải số!"
    print(f"2. Đã tách {X.shape[1]} cột đặc trưng và cột nhãn.")

    # 3. In min và max của tất cả các cột đặc trưng trong cùng một bảng
    bang_min_max = pd.DataFrame({
        "Min": X.min(),
        "Max": X.max()
    })
    print("\n3. Bảng Min và Max của các cột đặc trưng:")
    print(bang_min_max)

    # 4. Số dòng, số cột, kiểu từng cột
    print(f"\n4. Kích thước dữ liệu: {df.shape[0]} dòng, {df.shape[1]} cột")
    print("Kiểu dữ liệu từng cột:")
    print(df.dtypes)

    # 5. Số ô khuyết theo cột
    print("\n5. Số ô khuyết theo từng cột:")
    print(df.isna().sum())

    # 6. Số bản ghi trùng lặp hoàn toàn
    print(f"\n6. Số bản ghi trùng lặp hoàn toàn: {df.duplicated().sum()}")

    # 7. Phân bố lớp
    print("\n7. Phân bố các lớp:")
    print(df["Class"].value_counts())

    return df, X, y

def doi_chieu_va_ghi_bao_cao(df, X, y, duong_dan_bao_cao="bao_cao/Bao_Cao_DA14_DryBean_Buoc1.md"):
    # Thông số chuẩn ghi trong đề tài (Bộ dữ liệu Dry Bean - UCI ID 602)
    de_tai_chung = {
        "Số dòng": 13611,
        "Số cột": 17,
        "Số cột đặc trưng": 16,
        "Số giống đậu (lớp)": 7,
    }
    de_tai_lop = {
        "DERMASON": 3546,
        "SIRA": 2636,
        "SEKER": 2027,
        "HOROZ": 1928,
        "CALI": 1630,
        "BARBUNYA": 1322,
        "BOMBAY": 522,
    }

    # Tạo bảng đối chiếu kích thước chung
    thuc_te_chung = {
        "Số dòng": df.shape[0],
        "Số cột": df.shape[1],
        "Số cột đặc trưng": X.shape[1],
        "Số giống đậu (lớp)": y.nunique(),
    }
    bang_doi_chieu_chung = pd.DataFrame({
        "De_tai": pd.Series(de_tai_chung),
        "Thuc_te": pd.Series(thuc_te_chung),
    })
    bang_doi_chieu_chung["Chenh_lech"] = bang_doi_chieu_chung["Thuc_te"] - bang_doi_chieu_chung["De_tai"]

    # Tạo bảng đối chiếu số lượng từng giống đậu
    phan_bo_thuc_te = y.value_counts()
    bang_doi_chieu_lop = pd.DataFrame({
        "De_tai": pd.Series(de_tai_lop),
        "Thuc_te": phan_bo_thuc_te,
    }).fillna(0).astype(int)
    bang_doi_chieu_lop["Chenh_lech"] = bang_doi_chieu_lop["Thuc_te"] - bang_doi_chieu_lop["De_tai"]

    # In bảng đối chiếu ra màn hình
    print("\n=== ĐỐI CHIẾU VỚI KÍCH THƯỚC ĐỀ TÀI ===")
    print(bang_doi_chieu_chung)
    print("\n=== ĐỐI CHIẾU PHÂN BỐ TỪNG GIỐNG ĐẬU ===")
    print(bang_doi_chieu_lop)

    # Kiểm tra xem có chênh lệch nào không để tự động viết nhận xét
    co_lech = (bang_doi_chieu_chung["Chenh_lech"] != 0).any() or (bang_doi_chieu_lop["Chenh_lech"] != 0).any()
    if not co_lech:
        nhan_xet_doi_chieu = "Số liệu thực tế **khớp hoàn toàn 100%** với kích thước và phân bố lớp ghi trong đề tài (không có chênh lệch)."
    else:
        nhan_xet_doi_chieu = "**Có sự chênh lệch** giữa dữ liệu tải về và thông số đề tài (xem chi tiết tại cột `Chenh_lech` ở hai bảng trên)."

    # Chuẩn bị các bảng kiểm kê để ghi vào báo cáo
    bang_min_max = pd.DataFrame({"Min": X.min(), "Max": X.max()})
    bang_cot = pd.DataFrame({"Kieu_du_lieu": df.dtypes, "So_o_khuyet": df.isna().sum()})
    so_trung_lap = int(df.duplicated().sum())

    # Tự động tạo thư mục bao_cao (nếu chưa có) và ghi file
    Path(duong_dan_bao_cao).parent.mkdir(parents=True, exist_ok=True)
    with open(duong_dan_bao_cao, "w", encoding="utf-8") as f:
        f.write("# BÁO CÁO ĐỒ ÁN DA-14: BẢY GIỐNG ĐẬU KHÔ NHÌN TỪ BÓNG CỦA CHÚNG\n\n")
        f.write("## Bước 1: Nạp dữ liệu và kiểm kê trung thực\n\n")

        f.write("### 1.1. Kích thước, kiểu dữ liệu và số ô khuyết\n")
        f.write(f"- **Số dòng:** {df.shape[0]}\n")
        f.write(f"- **Số cột:** {df.shape[1]} (gồm {X.shape[1]} cột đặc trưng số và cột nhãn `Class` ở cuối)\n")
        f.write(f"- **Số bản ghi trùng lặp hoàn toàn:** {so_trung_lap}\n\n")
        f.write("```text\n" + bang_cot.to_string() + "\n```\n\n")

        f.write("### 1.2. Bảng giá trị Min và Max của 16 đặc trưng\n")
        f.write("```text\n" + bang_min_max.to_string() + "\n```\n\n")

        f.write("### 1.3. Đối chiếu số liệu với đề tài\n")
        f.write("```text\n" + bang_doi_chieu_chung.to_string() + "\n```\n\n")
        f.write("```text\n" + bang_doi_chieu_lop.to_string() + "\n```\n\n")
        f.write(f"- **Kết luận đối chiếu:** {nhan_xet_doi_chieu}\n")
        f.write(f"- **Ghi chú trùng lặp:** Phát hiện {so_trung_lap} dòng trùng hoàn toàn (giữ nguyên để bảo toàn đúng tập dữ liệu gốc của UCI).\n\n")

    print(f"\nĐã lưu toàn bộ kết quả kiểm kê và đối chiếu vào: {duong_dan_bao_cao}")

if __name__ == "__main__":
    doc_va_kiem_ke("data/raw/DryBeanDataset/Dry_Bean_Dataset.arff")
    df, X, y = doc_va_kiem_ke("data/raw/DryBeanDataset/Dry_Bean_Dataset.arff")
    doi_chieu_va_ghi_bao_cao(df, X, y)
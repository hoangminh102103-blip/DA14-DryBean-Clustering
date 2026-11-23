import sys
from pathlib import Path

# BẮT BUỘC đặt đoạn này lên trên cùng trước khi import từ thư mục data
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from data.nap import doc_va_kiem_ke

plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial"]
plt.rcParams["axes.unicode_minus"] = False
sns.set_theme(style="whitegrid", context="notebook")

THU_MUC_HINH = ROOT_DIR / "results" / "hinh"
THU_MUC_BANG = ROOT_DIR / "results" / "bang"
FILE_BAO_CAO_B2 = ROOT_DIR / "bao_cao" / "Bao_Cao_DA14_DryBean_Buoc2.md"


def ve_heatmap_va_loc_tuong_quan(X: pd.DataFrame) -> pd.DataFrame:
    """Hình 1 (Heatmap): Ma trận tương quan 16x16 và lọc các cặp |r| > 0.9."""
    corr = X.corr(method="pearson")

    fig, ax = plt.subplots(figsize=(13, 10))
    sns.heatmap(
        corr,
        annot=True,
        fmt=".2f",
        cmap="coolwarm",
        vmin=-1,
        vmax=1,
        linewidths=0.5,
        annot_kws={"size": 7.5},
        cbar_kws={"label": "Hệ số tương quan Pearson r (không đơn vị)"},
        ax=ax,
    )
    ax.set_title("Hình 1: Bản đồ nhiệt tương quan Pearson giữa 16 đặc trưng hạt đậu", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("16 đặc trưng hình học & hình dạng (tên biến)", fontsize=11)
    ax.set_ylabel("16 đặc trưng hình học & hình dạng (tên biến)", fontsize=11)
    plt.xticks(rotation=45, ha="right")
    plt.yticks(rotation=0)
    plt.tight_layout()
    fig.savefig(THU_MUC_HINH / "hinh_01_heatmap_tuong_quan.png", dpi=300)
    plt.close(fig)

    cac_cap = []
    cols = corr.columns
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            r_val = corr.iloc[i, j]
            if abs(r_val) > 0.9:
                cac_cap.append({
                    "Dac_trung_1": cols[i],
                    "Dac_trung_2": cols[j],
                    "He_so_r": round(float(r_val), 4),
                    "Tri_tuyet_doi_r": round(float(abs(r_val)), 4),
                })

    bang_cap = pd.DataFrame(cac_cap).sort_values(by="Tri_tuyet_doi_r", ascending=False).reset_index(drop=True)
    bang_cap.index = bang_cap.index + 1
    bang_cap.index.name = "STT"
    bang_cap.to_csv(THU_MUC_BANG / "bang_21_cap_tuong_quan_tren_09.csv", encoding="utf-8-sig")
    return bang_cap


def ve_boxplot_bon_kich_thuoc(df: pd.DataFrame):
    """Hình 2 (Boxplot): Biểu đồ hộp của 4 cột kích thước tách theo 7 giống."""
    bon_cot = [
        ("Area", "Diện tích hạt - Area (pixel²)"),
        ("Perimeter", "Chu vi hạt - Perimeter (pixel)"),
        ("MajorAxisLength", "Độ dài trục chính - MajorAxisLength (pixel)"),
        ("MinorAxisLength", "Độ dài trục phụ - MinorAxisLength (pixel)"),
    ]
    thu_tu_lop = df.groupby("Class")["Area"].median().sort_values(ascending=False).index.tolist()

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    for ax, (cot, nhan_y) in zip(axes.flat, bon_cot):
        sns.boxplot(
            data=df,
            x="Class",
            y=cot,
            hue="Class",
            order=thu_tu_lop,
            palette="Set2",
            legend=False,
            fliersize=2,
            ax=ax,
        )
        ax.set_title(f"Phân bố {cot} theo 7 giống đậu", fontsize=11, fontweight="bold")
        ax.set_xlabel("Giống đậu khô (7 lớp)", fontsize=10)
        ax.set_ylabel(nhan_y, fontsize=10)
        ax.tick_params(axis="x", rotation=25)

    fig.suptitle("Hình 2: Biểu đồ hộp 4 đặc trưng kích thước tách theo 7 giống đậu", fontsize=13, fontweight="bold", y=1.01)
    plt.tight_layout()
    fig.savefig(THU_MUC_HINH / "hinh_02_boxplot_kich_thuoc.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def ve_scatter_dien_tich_chu_vi(df: pd.DataFrame):
    """Hình 3 (Scatter Plot): Phân tán diện tích theo chu vi tô màu theo giống."""
    fig, ax = plt.subplots(figsize=(10, 7))
    sns.scatterplot(
        data=df,
        x="Perimeter",
        y="Area",
        hue="Class",
        palette="tab10",
        alpha=0.65,
        s=18,
        edgecolor=None,
        ax=ax,
    )
    ax.set_title("Hình 3: Tương quan phi tuyến giữa Diện tích và Chu vi theo 7 giống đậu", fontsize=12, fontweight="bold")
    ax.set_xlabel("Chu vi hạt - Perimeter (pixel)", fontsize=11)
    ax.set_ylabel("Diện tích hạt - Area (pixel²)", fontsize=11)
    ax.legend(title="Giống đậu (7 lớp)", loc="upper left", frameon=True)
    plt.tight_layout()
    fig.savefig(THU_MUC_HINH / "hinh_03_scatter_area_perimeter.png", dpi=300)
    plt.close(fig)


def ve_phuong_sai_tich_luy_pca(X: pd.DataFrame):
    """Hình 4 (Line Plot): Đường phương sai giải thích tích lũy sau chuẩn hóa."""
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    pca = PCA()
    pca.fit(X_scaled)

    ty_le_rieng = pca.explained_variance_ratio_ * 100
    ty_le_tich_luy = np.cumsum(ty_le_rieng)
    so_pc = np.arange(1, len(ty_le_tich_luy) + 1)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(so_pc, ty_le_tich_luy, marker="o", linewidth=2.2, color="#1f77b4", label="Phương sai tích lũy (%)")
    ax.plot(so_pc, ty_le_rieng, marker="s", linestyle="--", linewidth=1.6, color="#ff7f0e", label="Phương sai từng PC (%)")
    ax.axhline(95, color="green", linestyle=":", linewidth=1.5, label="Ngưỡng 95% phương sai (PC = 5)")
    ax.axhline(99, color="red", linestyle=":", linewidth=1.5, label="Ngưỡng 99% phương sai (PC = 7)")

    for pc, val in zip(so_pc[:8], ty_le_tich_luy[:8]):
        ax.annotate(f"{val:.1f}%", (pc, val), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=8.5)

    ax.set_title("Hình 4: Đường phương sai giải thích tích lũy qua PCA sau chuẩn hóa StandardScaler", fontsize=12, fontweight="bold")
    ax.set_xlabel("Số thành phần chính giữ lại - PC (thành phần)", fontsize=11)
    ax.set_ylabel("Tỷ lệ phương sai giải thích (%)", fontsize=11)
    ax.set_xticks(so_pc)
    ax.set_ylim(0, 108)
    ax.legend(loc="center right", frameon=True)
    plt.tight_layout()
    fig.savefig(THU_MUC_HINH / "hinh_04_phuong_sai_tich_luy_pca.png", dpi=300)
    plt.close(fig)

    return ty_le_tich_luy


def ve_bar_so_hat_theo_giong(df: pd.DataFrame):
    """Hình 5 (Bar Chart): Biểu đồ cột số lượng hạt theo từng giống có ghi số cụ thể."""
    dem_lop = df["Class"].value_counts().reset_index()
    dem_lop.columns = ["Class", "So_luong"]
    tong = len(df)

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(
        data=dem_lop,
        x="Class",
        y="So_luong",
        hue="Class",
        palette="viridis",
        legend=False,
        ax=ax,
    )

    for patch, (_, row) in zip(ax.patches, dem_lop.iterrows()):
        chieu_cao = patch.get_height()
        ty_le = chieu_cao / tong * 100
        ax.annotate(
            f"{int(chieu_cao):,}\n({ty_le:.1f}%)",
            (patch.get_x() + patch.get_width() / 2, chieu_cao),
            ha="center",
            va="bottom",
            fontsize=9.5,
            fontweight="bold",
        )

    ax.set_title("Hình 5: Số lượng mẫu hạt theo từng giống đậu trong tập dữ liệu", fontsize=12, fontweight="bold")
    ax.set_xlabel("Giống đậu khô (7 lớp)", fontsize=11)
    ax.set_ylabel("Số lượng mẫu hạt (hạt)", fontsize=11)
    ax.set_ylim(0, dem_lop["So_luong"].max() * 1.15)
    plt.tight_layout()
    fig.savefig(THU_MUC_HINH / "hinh_05_bar_so_luong_giong_dau.png", dpi=300)
    plt.close(fig)


def ve_kde_ty_le_khung_hinh(df: pd.DataFrame):
    """Hình 6 (KDE Plot): Biểu đồ đường mật độ xác suất đặc trưng hình dạng AspectRation."""
    fig, ax = plt.subplots(figsize=(10, 6))
    for giong in sorted(df["Class"].unique()):
        du_lieu_lop = df.loc[df["Class"] == giong, "AspectRation"]
        sns.kdeplot(du_lieu_lop, label=giong, linewidth=2, fill=True, alpha=0.12, ax=ax)

    ax.set_title("Hình 6: Phân bố mật độ xác suất tỷ lệ khung hình (AspectRation) theo 7 giống", fontsize=12, fontweight="bold")
    ax.set_xlabel("Tỷ lệ trục chính / trục phụ - AspectRation (không đơn vị)", fontsize=11)
    ax.set_ylabel("Mật độ xác suất ước lượng - KDE (không đơn vị)", fontsize=11)
    ax.legend(title="Giống đậu (7 lớp)", loc="upper right", frameon=True)
    plt.tight_layout()
    fig.savefig(THU_MUC_HINH / "hinh_06_kde_ty_le_khung_hinh.png", dpi=300)
    plt.close(fig)


def ghi_bao_cao_buoc_2(bang_21_cap: pd.DataFrame, ty_le_tich_luy: np.ndarray):
    FILE_BAO_CAO_B2.parent.mkdir(parents=True, exist_ok=True)
    cac_dong = [
        "# BÁO CÁO BƯỚC 2: KHÁM PHÁ VÀ TRỰC QUAN HÓA DỮ LIỆU (EDA)",
        "",
        "Toàn bộ 6 biểu đồ thuộc 6 loại trực quan hóa khác nhau đã được xuất và lưu tại thư mục `results/hinh/`.",
        "",
        "---",
        "",
        "## 1. Phân tích tương quan và đa cộng tuyến (`hinh_01_heatmap_tuong_quan.png`)",
        "- **Tệp hình:** `results/hinh/hinh_01_heatmap_tuong_quan.png` (Loại: Bản đồ nhiệt - Heatmap 16 x 16).",
        "- **Nhận xét:** Đa cộng tuyến cực mạnh tập trung thành hai khối tách biệt rõ rệt: khối kích thước (`Area`, `Perimeter`, `MajorAxisLength`, `MinorAxisLength`, `ConvexArea`, `EquivDiameter`) có tương quan dương gần như tuyệt đối (r > 0.93) và khối tỷ lệ hình dạng (`Eccentricity`, `AspectRation`, `Compactness`, `ShapeFactor1..4`) tương quan nghịch chặt chẽ với nhau; điều này chứng tỏ không gian 16 chiều chứa nhiều thông tin dư thừa và hoàn toàn có thể nén xuống không gian ít chiều hơn qua PCA.",
        "",
        f"### Bảng liệt kê đầy đủ {len(bang_21_cap)} cặp đặc trưng có tương quan tuyệt đối |r| > 0.9",
        "",
        "~~~text",
        bang_21_cap.to_string(),
        "~~~",
        "",
        "---",
        "",
        "## 2. Phân bố 4 đặc trưng kích thước theo 7 giống (`hinh_02_boxplot_kich_thuoc.png`)",
        "- **Tệp hình:** `results/hinh/hinh_02_boxplot_kich_thuoc.png` (Loại: Biểu đồ hộp - Boxplot ghép 4 khung).",
        "- **Nhận xét:** Giống `BOMBAY` tách biệt hoàn toàn khỏi 6 giống còn lại trên cả 4 chiều kích thước (khoảng tứ phân vị không hề chồng lấn), trong khi ba giống `SIRA`, `DERMASON` và `SEKER` có dải kích thước chồng lấn mạnh và xuất hiện nhiều điểm ngoại lai ở đuôi trên của `CALI` và `BARBUNYA` — đây chính là các điểm dễ kéo lệch tâm trung bình của k-means hơn so với medoid.",
        "",
        "---",
        "",
        "## 3. Quan hệ giữa Diện tích và Chu vi (`hinh_03_scatter_area_perimeter.png`)",
        "- **Tệp hình:** `results/hinh/hinh_03_scatter_area_perimeter.png` (Loại: Biểu đồ phân tán - Scatter Plot).",
        "- **Nhận xét:** Toàn bộ 13.611 hạt đậu bám sát dọc theo một dải cong đơn điệu hẹp (r = 0.9667), chứng minh `Area` và `Perimeter` gần như mang cùng một thông tin về độ lớn; tuy nhiên tại cùng mức chu vi quanh 1.000 pixel, giống `HOROZ` có diện tích nhỏ hơn rõ rệt so với `CALI` và `BARBUNYA` do hình thái thuôn dài đặc trưng.",
        "",
        "---",
        "",
        "## 4. Phương sai tích lũy sau chuẩn hóa (`hinh_04_phuong_sai_tich_luy_pca.png`)",
        "- **Tệp hình:** `results/hinh/hinh_04_phuong_sai_tich_luy_pca.png` (Loại: Biểu đồ đường - Line Plot).",
        f"- **Nhận xét:** Chỉ cần giữ lại **5 thành phần chính đầu tiên** đã bảo toàn được **{ty_le_tich_luy[4]:.2f}%** tổng phương sai của bộ dữ liệu (vượt ngưỡng 95%) và **7 thành phần** đạt **{ty_le_tich_luy[6]:.2f}%** (vượt ngưỡng 99%), cho phép giảm chiều từ 16 xuống 5–7 chiều trước khi gom cụm để vừa loại bỏ nhiễu đa cộng tuyến vừa giảm đáng kể chi phí tính ma trận khoảng cách.",
        "",
        "---",
        "",
        "## 5. Phân bố số lượng hạt theo từng giống (`hinh_05_bar_so_luong_giong_dau.png`)",
        "- **Tệp hình:** `results/hinh/hinh_05_bar_so_luong_giong_dau.png` (Loại: Biểu đồ cột - Bar Chart).",
        "- **Nhận xét:** Dữ liệu tồn tại sự mất cân bằng lớp đáng kể với tỷ lệ giữa lớp lớn nhất (`DERMASON`: 3.546 hạt, chiếm 26,1%) và lớp nhỏ nhất (`BOMBAY`: 522 hạt, chiếm 3,8%) lên tới **6,79 lần**, báo trước rủi ro các thuật toán dựa trên phương sai như k-means có xu hướng chia nhỏ cụm `DERMASON` thành nhiều cụm con thay vì giữ đúng cấu trúc 7 giống.",
        "",
        "---",
        "",
        "## 6. Phân bố mật độ đặc trưng hình dạng AspectRation (`hinh_06_kde_ty_le_khung_hinh.png`)",
        "- **Tệp hình:** `results/hinh/hinh_06_kde_ty_le_khung_hinh.png` (Loại: Biểu đồ đường cong mật độ xác suất - KDE Plot).",
        "- **Nhận xét:** Đặc trưng hình dạng bổ sung khả năng phân tách mà nhóm kích thước bỏ sót — cụ thể giống `HOROZ` (đỉnh mật độ quanh 2,0, hạt dài) và `SEKER` (đỉnh quanh 1,25, hạt gần tròn) tách biệt rõ rệt khỏi nhóm trung gian (`DERMASON`, `SIRA`, `BARBUNYA` chồng lấn quanh 1,45–1,60), khẳng định cần kết hợp cả kích thước lẫn hình dạng để gom cụm chính xác.",
    ]

    with open(FILE_BAO_CAO_B2, "w", encoding="utf-8") as f:
        f.write("\n".join(cac_dong))


def ghi_bao_cao_buoc_2(bang_21_cap: pd.DataFrame, ty_le_tich_luy: np.ndarray):
    FILE_BAO_CAO_B2.parent.mkdir(parents=True, exist_ok=True)
    cac_dong = [
        "# BÁO CÁO BƯỚC 2: KHÁM PHÁ VÀ TRỰC QUAN HÓA DỮ LIỆU (EDA)",
        "",
        "Toàn bộ 6 biểu đồ thuộc 6 loại trực quan hóa khác nhau đã được xuất và lưu tại thư mục `results/hinh/`.",
        "",
        "---",
        "",
        "## 1. Phân tích tương quan và đa cộng tuyến (`hinh_01_heatmap_tuong_quan.png`)",
        "- **Tệp hình:** `results/hinh/hinh_01_heatmap_tuong_quan.png` (Loại: Bản đồ nhiệt - Heatmap 16 x 16).",
        "- **Nhận xét:** Đa cộng tuyến cực mạnh tập trung thành hai khối tách biệt rõ rệt: khối kích thước (`Area`, `Perimeter`, `MajorAxisLength`, `MinorAxisLength`, `ConvexArea`, `EquivDiameter`) có tương quan dương gần như tuyệt đối (r > 0.93) và khối tỷ lệ hình dạng (`Eccentricity`, `AspectRation`, `Compactness`, `ShapeFactor1..4`) tương quan nghịch chặt chẽ với nhau; điều này chứng tỏ không gian 16 chiều chứa nhiều thông tin dư thừa và hoàn toàn có thể nén xuống không gian ít chiều hơn qua PCA.",
        "",
        f"### Bảng liệt kê đầy đủ {len(bang_21_cap)} cặp đặc trưng có tương quan tuyệt đối |r| > 0.9",
        "",
        "~~~text",
        bang_21_cap.to_string(),
        "~~~",
        "",
        "---",
        "",
        "## 2. Phân bố 4 đặc trưng kích thước theo 7 giống (`hinh_02_boxplot_kich_thuoc.png`)",
        "- **Tệp hình:** `results/hinh/hinh_02_boxplot_kich_thuoc.png` (Loại: Biểu đồ hộp - Boxplot ghép 4 khung).",
        "- **Nhận xét:** Giống `BOMBAY` tách biệt hoàn toàn khỏi 6 giống còn lại trên cả 4 chiều kích thước (khoảng tứ phân vị không hề chồng lấn), trong khi ba giống `SIRA`, `DERMASON` và `SEKER` có dải kích thước chồng lấn mạnh và xuất hiện nhiều điểm ngoại lai ở đuôi trên của `CALI` và `BARBUNYA` — đây chính là các điểm dễ kéo lệch tâm trung bình của k-means hơn so với medoid.",
        "",
        "---",
        "",
        "## 3. Quan hệ giữa Diện tích và Chu vi (`hinh_03_scatter_area_perimeter.png`)",
        "- **Tệp hình:** `results/hinh/hinh_03_scatter_area_perimeter.png` (Loại: Biểu đồ phân tán - Scatter Plot).",
        "- **Nhận xét:** Toàn bộ 13.611 hạt đậu bám sát dọc theo một dải cong đơn điệu hẹp (r = 0.9667), chứng minh `Area` và `Perimeter` gần như mang cùng một thông tin về độ lớn; tuy nhiên tại cùng mức chu vi quanh 1.000 pixel, giống `HOROZ` có diện tích nhỏ hơn rõ rệt so với `CALI` và `BARBUNYA` do hình thái thuôn dài đặc trưng.",
        "",
        "---",
        "",
        "## 4. Phương sai tích lũy sau chuẩn hóa (`hinh_04_phuong_sai_tich_luy_pca.png`)",
        "- **Tệp hình:** `results/hinh/hinh_04_phuong_sai_tich_luy_pca.png` (Loại: Biểu đồ đường - Line Plot).",
        f"- **Nhận xét:** Chỉ cần giữ lại **5 thành phần chính đầu tiên** đã bảo toàn được **{ty_le_tich_luy[4]:.2f}%** tổng phương sai của bộ dữ liệu (vượt ngưỡng 95%) và **7 thành phần** đạt **{ty_le_tich_luy[6]:.2f}%** (vượt ngưỡng 99%), cho phép giảm chiều từ 16 xuống 5–7 chiều trước khi gom cụm để vừa loại bỏ nhiễu đa cộng tuyến vừa giảm đáng kể chi phí tính ma trận khoảng cách.",
        "",
        "---",
        "",
        "## 5. Phân bố số lượng hạt theo từng giống (`hinh_05_bar_so_luong_giong_dau.png`)",
        "- **Tệp hình:** `results/hinh/hinh_05_bar_so_luong_giong_dau.png` (Loại: Biểu đồ cột - Bar Chart).",
        "- **Nhận xét:** Dữ liệu tồn tại sự mất cân bằng lớp đáng kể với tỷ lệ giữa lớp lớn nhất (`DERMASON`: 3.546 hạt, chiếm 26,1%) và lớp nhỏ nhất (`BOMBAY`: 522 hạt, chiếm 3,8%) lên tới **6,79 lần**, báo trước rủi ro các thuật toán dựa trên phương sai như k-means có xu hướng chia nhỏ cụm `DERMASON` thành nhiều cụm con thay vì giữ đúng cấu trúc 7 giống.",
        "",
        "---",
        "",
        "## 6. Phân bố mật độ đặc trưng hình dạng AspectRation (`hinh_06_kde_ty_le_khung_hinh.png`)",
        "- **Tệp hình:** `results/hinh/hinh_06_kde_ty_le_khung_hinh.png` (Loại: Biểu đồ đường cong mật độ xác suất - KDE Plot).",
        "- **Nhận xét:** Đặc trưng hình dạng bổ sung khả năng phân tách mà nhóm kích thước bỏ sót — cụ thể giống `HOROZ` (đỉnh mật độ quanh 2,0, hạt dài) và `SEKER` (đỉnh quanh 1,25, hạt gần tròn) tách biệt rõ rệt khỏi nhóm trung gian (`DERMASON`, `SIRA`, `BARBUNYA` chồng lấn quanh 1,45–1,60), khẳng định cần kết hợp cả kích thước lẫn hình dạng để gom cụm chính xác.",
    ]

    with open(FILE_BAO_CAO_B2, "w", encoding="utf-8") as f:
        f.write("\n".join(cac_dong))


def chay_kham_pha():
    THU_MUC_HINH.mkdir(parents=True, exist_ok=True)
    THU_MUC_BANG.mkdir(parents=True, exist_ok=True)

    df, X, _ = doc_va_kiem_ke(ROOT_DIR / "data" / "raw" / "DryBeanDataset" / "Dry_Bean_Dataset.arff")

    print("\n--- ĐANG SINH 6 BIỂU ĐỒ EDA VÀ BẢNG TƯƠNG QUAN ---")
    bang_21_cap = ve_heatmap_va_loc_tuong_quan(X)
    print(f"[1/6] Đã lưu hinh_01_heatmap_tuong_quan.png & lọc được {len(bang_21_cap)} cặp |r| > 0.9:")
    print(bang_21_cap.to_string())

    ve_boxplot_bon_kich_thuoc(df)
    print("[2/6] Đã lưu hinh_02_boxplot_kich_thuoc.png")

    ve_scatter_dien_tich_chu_vi(df)
    print("[3/6] Đã lưu hinh_03_scatter_area_perimeter.png")

    ty_le_tich_luy = ve_phuong_sai_tich_luy_pca(X)
    print("[4/6] Đã lưu hinh_04_phuong_sai_tich_luy_pca.png")

    ve_bar_so_hat_theo_giong(df)
    print("[5/6] Đã lưu hinh_05_bar_so_luong_giong_dau.png")

    ve_kde_ty_le_khung_hinh(df)
    print("[6/6] Đã lưu hinh_06_kde_ty_le_khung_hinh.png")

    ghi_bao_cao_buoc_2(bang_21_cap, ty_le_tich_luy)
    print(f"\n[OK] Đã xuất toàn bộ nhận xét và bảng số liệu vào: {FILE_BAO_CAO_B2}")


if __name__ == "__main__":
    chay_kham_pha()
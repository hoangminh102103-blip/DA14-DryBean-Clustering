import sys
from pathlib import Path

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


def ve_heatmap_va_loc_tuong_quan(X: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
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
    return corr, bang_cap


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


def ve_scatter_dien_tich_chu_vi(df: pd.DataFrame, r_area_perim: float):
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
    ax.set_title(
        f"Hình 3: Quan hệ gần tuyến tính giữa Diện tích và Chu vi theo 7 giống đậu (r = {r_area_perim:.4f})",
        fontsize=12,
        fontweight="bold",
    )
    ax.set_xlabel("Chu vi hạt - Perimeter (pixel)", fontsize=11)
    ax.set_ylabel("Diện tích hạt - Area (pixel²)", fontsize=11)
    ax.legend(title="Giống đậu (7 lớp)", loc="upper left", frameon=True)
    plt.tight_layout()
    fig.savefig(THU_MUC_HINH / "hinh_03_scatter_area_perimeter.png", dpi=300)
    plt.close(fig)


def ve_phuong_sai_tich_luy_pca(X: pd.DataFrame) -> tuple[np.ndarray, pd.DataFrame]:
    """Hình 4 (Line Plot): Đường phương sai giải thích tích lũy (chỉ mô tả EDA)."""
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    pca = PCA()
    pca.fit(X_scaled)

    ty_le_rieng = pca.explained_variance_ratio_ * 100
    ty_le_tich_luy = np.cumsum(ty_le_rieng)
    so_pc = np.arange(1, len(ty_le_tich_luy) + 1)

    cac_moc = [80, 90, 95, 99]
    k_moc = np.searchsorted(ty_le_tich_luy, cac_moc) + 1
    bang_moc_pca = pd.DataFrame({
        "Nguong_phuong_sai": [f">= {m}%" for m in cac_moc],
        "So_PC_toi_thieu_k": k_moc,
        "Phuong_sai_tich_luy": [f"{ty_le_tich_luy[k - 1]:.2f}%" for k in k_moc],
    })

    k_95 = int(k_moc[2])
    k_99 = int(k_moc[3])

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(so_pc, ty_le_tich_luy, marker="o", linewidth=2.2, color="#1f77b4", label="Phương sai tích lũy (%)")
    ax.plot(so_pc, ty_le_rieng, marker="s", linestyle="--", linewidth=1.6, color="#ff7f0e", label="Phương sai từng PC (%)")
    ax.axhline(95, color="green", linestyle=":", linewidth=1.5, label=f"Ngưỡng 95% (PC = {k_95}, đạt {ty_le_tich_luy[k_95 - 1]:.2f}%)")
    ax.axhline(99, color="red", linestyle=":", linewidth=1.5, label=f"Ngưỡng 99% (PC = {k_99}, đạt {ty_le_tich_luy[k_99 - 1]:.2f}%)")

    for pc, val in zip(so_pc[:8], ty_le_tich_luy[:8]):
        ax.annotate(f"{val:.2f}%", (pc, val), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=8.5)

    ax.set_title("Hình 4: Đường phương sai giải thích tích lũy qua PCA (EDA mô tả trên toàn bộ dữ liệu)", fontsize=11.5, fontweight="bold")
    ax.set_xlabel("Số thành phần chính giữ lại - PC (thành phần)", fontsize=11)
    ax.set_ylabel("Tỷ lệ phương sai giải thích (%)", fontsize=11)
    ax.set_xticks(so_pc)
    ax.set_ylim(0, 108)
    ax.legend(loc="center right", frameon=True)
    plt.tight_layout()
    fig.savefig(THU_MUC_HINH / "hinh_04_phuong_sai_tich_luy_pca.png", dpi=300)
    plt.close(fig)

    return ty_le_tich_luy, bang_moc_pca


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


def ghi_bao_cao_buoc_2(
    df: pd.DataFrame,
    corr: pd.DataFrame,
    bang_21_cap: pd.DataFrame,
    ty_le_tich_luy: np.ndarray,
    bang_moc_pca: pd.DataFrame,
):
    FILE_BAO_CAO_B2.parent.mkdir(parents=True, exist_ok=True)

    # Tính động toàn bộ số liệu cho câu nhận xét của từng hình
    nhom_kich_thuoc = ["Area", "Perimeter", "MajorAxisLength", "MinorAxisLength", "ConvexArea", "EquivDiameter"]
    ma_tran_kt = corr.loc[nhom_kich_thuoc, nhom_kich_thuoc].values
    r_kt_min = float(ma_tran_kt[~np.eye(len(nhom_kich_thuoc), dtype=bool)].min())
    r_cap_min = float(bang_21_cap["Tri_tuyet_doi_r"].min())
    r_cap_max = float(bang_21_cap["Tri_tuyet_doi_r"].max())
    r_sf1_minor = float(corr.loc["ShapeFactor1", "MinorAxisLength"])
    r_sf1_aspect = float(corr.loc["ShapeFactor1", "AspectRation"])
    r_aspect_comp = float(corr.loc["AspectRation", "Compactness"])

    # Số liệu Hình 2 (IQR Area & ngoại lai đuôi trên)
    q25 = df.groupby("Class")["Area"].quantile(0.25)
    q75 = df.groupby("Class")["Area"].quantile(0.75)
    upper_fence = q75 + 1.5 * (q75 - q25)
    so_ngoai_lai = {
        lop: int((df.loc[df["Class"] == lop, "Area"] > upper_fence[lop]).sum())
        for lop in q25.index
    }

    # Số liệu Hình 3
    r_area_perim = float(corr.loc["Area", "Perimeter"])

    # Số liệu Hình 4
    k_vals = bang_moc_pca["So_PC_toi_thieu_k"].tolist()

    # Số liệu Hình 5
    dem_lop = df["Class"].value_counts()
    lop_max, so_max = dem_lop.index[0], int(dem_lop.iloc[0])
    lop_min, so_min = dem_lop.index[-1], int(dem_lop.iloc[-1])
    ty_le_lech = so_max / so_min

    # Số liệu Hình 6
    med_aspect = df.groupby("Class")["AspectRation"].median()

    cac_dong = [
        "# BÁO CÁO BƯỚC 2: KHÁM PHÁ VÀ TRỰC QUAN HÓA DỮ LIỆU (EDA)",
        "",
        "Toàn bộ 6 biểu đồ thuộc 6 loại trực quan hóa khác nhau đã được xuất và lưu tại thư mục `results/hinh/`.",
        "",
        "---",
        "",
        "## 1. Phân tích tương quan và đa cộng tuyến (`hinh_01_heatmap_tuong_quan.png`)",
        "- **Tệp hình:** `results/hinh/hinh_01_heatmap_tuong_quan.png` (Loại: Bản đồ nhiệt - Heatmap 16 × 16).",
        f"- **Nhận xét:** Đa cộng tuyến tập trung mạnh ở nhóm 6 biến kích thước ($r \ge {r_kt_min:.4f}$), nhóm biến hình dạng (`AspectRation`–`Compactness` đạt $r = {r_aspect_comp:.4f}$) và `ShapeFactor1` tương quan nghịch với nhóm kích thước ($r = {r_sf1_minor:.4f}$ với `MinorAxisLength`, trong khi gần độc lập với `AspectRation` ở $r = {r_sf1_aspect:.4f}$), tạo thành đúng {len(bang_21_cap)} cặp có $\vert r\vert \in [{r_cap_min:.4f}, {r_cap_max:.4f}]$.",
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
        f"- **Nhận xét:** Trên `Area`, giống `BOMBAY` (IQR {q25['BOMBAY']/1000:.1f}k–{q75['BOMBAY']/1000:.1f}k) tách biệt hoàn toàn khỏi 6 giống còn lại, `DERMASON` ({q25['DERMASON']/1000:.1f}k–{q75['DERMASON']/1000:.1f}k) không giao với `SEKER` ({q25['SEKER']/1000:.1f}k–{q75['SEKER']/1000:.1f}k) mà chỉ `SEKER`–`SIRA` ({q25['SIRA']/1000:.1f}k–{q75['SIRA']/1000:.1f}k) chạm nhẹ, đồng thời xuất hiện nhiều ngoại lai đuôi trên ở `SEKER` ({so_ngoai_lai['SEKER']} điểm), `CALI` ({so_ngoai_lai['CALI']} điểm), `SIRA` ({so_ngoai_lai['SIRA']} điểm) và `BARBUNYA` ({so_ngoai_lai['BARBUNYA']} điểm).",
        "",
        "---",
        "",
        "## 3. Quan hệ giữa Diện tích và Chu vi (`hinh_03_scatter_area_perimeter.png`)",
        "- **Tệp hình:** `results/hinh/hinh_03_scatter_area_perimeter.png` (Loại: Biểu đồ phân tán - Scatter Plot).",
        f"- **Nhận xét:** `Area` và `Perimeter` thể hiện quan hệ đồng biến gần tuyến tính rất chặt ($r = {r_area_perim:.4f}$) dọc theo một dải hẹp, trong đó giống thuôn dài `HOROZ` nằm thấp hơn về diện tích so với `CALI` và `BARBUNYA` ở cùng mức chu vi.",
        "",
        "---",
        "",
        "## 4. Phương sai tích lũy sau chuẩn hóa (`hinh_04_phuong_sai_tich_luy_pca.png`)",
        "- **Tệp hình:** `results/hinh/hinh_04_phuong_sai_tich_luy_pca.png` (Loại: Biểu đồ đường - Line Plot).",
        f"- **Nhận xét:** Số thành phần chính tối thiểu đạt các ngưỡng phương sai 80%, 90%, 95% và 99% lần lượt là **k = {k_vals[0]}, {k_vals[1]}, {k_vals[2]}, {k_vals[3]}** (4 PC đạt {ty_le_tich_luy[3]:.2f}%, 5 PC đạt {ty_le_tich_luy[4]:.2f}%, 7 PC đạt {ty_le_tich_luy[6]:.2f}% — lưu ý kết quả fit trên toàn bộ tập dữ liệu này chỉ phục vụ EDA mô tả, không dùng để chọn tham số $k$ cho thực nghiệm).",
        "",
        "### Bảng số thành phần chính tối thiểu theo 4 ngưỡng phương sai (tính bằng `np.searchsorted`)",
        "",
        "~~~text",
        bang_moc_pca.to_string(index=False),
        "~~~",
        "",
        "---",
        "",
        "## 5. Phân bố số lượng hạt theo từng giống (`hinh_05_bar_so_luong_giong_dau.png`)",
        "- **Tệp hình:** `results/hinh/hinh_05_bar_so_luong_giong_dau.png` (Loại: Biểu đồ cột - Bar Chart).",
        f"- **Nhận xét:** Tập dữ liệu mất cân bằng lớp rõ rệt với tỷ lệ chênh lệch giữa lớp lớn nhất (`{lop_max}`: {so_max:,} hạt, {so_max/len(df)*100:.2f}%) và lớp nhỏ nhất (`{lop_min}`: {so_min:,} hạt, {so_min/len(df)*100:.2f}%) lên tới **{ty_le_lech:.2f} lần**.",
        "",
        "---",
        "",
        "## 6. Phân bố mật độ đặc trưng hình dạng AspectRation (`hinh_06_kde_ty_le_khung_hinh.png`)",
        "- **Tệp hình:** `results/hinh/hinh_06_kde_ty_le_khung_hinh.png` (Loại: Biểu đồ đường cong mật độ xác suất - KDE Plot).",
        f"- **Nhận xét:** Đặc trưng hình dạng `AspectRation` tách biệt rõ giống hạt dài `HOROZ` (trung vị {med_aspect['HOROZ']:.2f}) và hạt tròn `SEKER` (trung vị {med_aspect['SEKER']:.2f}) khỏi nhóm trung gian `DERMASON` ({med_aspect['DERMASON']:.2f}), `BARBUNYA` ({med_aspect['BARBUNYA']:.2f}) và `SIRA` ({med_aspect['SIRA']:.2f}).",
    ]

    with open(FILE_BAO_CAO_B2, "w", encoding="utf-8") as f:
        f.write("\n".join(cac_dong))


def chay_kham_pha():
    THU_MUC_HINH.mkdir(parents=True, exist_ok=True)
    THU_MUC_BANG.mkdir(parents=True, exist_ok=True)

    df, X, _ = doc_va_kiem_ke(ROOT_DIR / "data" / "raw" / "DryBeanDataset" / "Dry_Bean_Dataset.arff")

    print("\n--- ĐANG SINH 6 BIỂU ĐỒ EDA VÀ BẢNG TƯƠNG QUAN ---")
    corr, bang_21_cap = ve_heatmap_va_loc_tuong_quan(X)
    print(f"[1/6] Đã lưu hinh_01_heatmap_tuong_quan.png & lọc được {len(bang_21_cap)} cặp |r| > 0.9.")

    ve_boxplot_bon_kich_thuoc(df)
    print("[2/6] Đã lưu hinh_02_boxplot_kich_thuoc.png")

    r_area_perim = float(corr.loc["Area", "Perimeter"])
    ve_scatter_dien_tich_chu_vi(df, r_area_perim)
    print("[3/6] Đã lưu hinh_03_scatter_area_perimeter.png")

    ty_le_tich_luy, bang_moc_pca = ve_phuong_sai_tich_luy_pca(X)
    print("[4/6] Đã lưu hinh_04_phuong_sai_tich_luy_pca.png | Bảng 4 mốc PCA:")
    print(bang_moc_pca.to_string(index=False))

    ve_bar_so_hat_theo_giong(df)
    print("[5/6] Đã lưu hinh_05_bar_so_luong_giong_dau.png")

    ve_kde_ty_le_khung_hinh(df)
    print("[6/6] Đã lưu hinh_06_kde_ty_le_khung_hinh.png")

    ghi_bao_cao_buoc_2(df, corr, bang_21_cap, ty_le_tich_luy, bang_moc_pca)
    print(f"\nĐã xuất toàn bộ nhận xét và bảng số liệu vào: {FILE_BAO_CAO_B2}")


if __name__ == "__main__":
    chay_kham_pha()
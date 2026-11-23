# DA14-DryBean: Phân cụm 7 giống đậu khô (Mean vs. Medoid)

Đồ án kết thúc học phần: **DA-14 — Bảy giống đậu khô nhìn từ bóng của chúng: tâm trung bình hay medoid?**

## 1. Tải và chuẩn bị dữ liệu

1. Truy cập kho dữ liệu UCI và tải bộ **Dry Bean Dataset**:
   - **Link tải:** https://archive.ics.uci.edu/dataset/602/dry+bean+dataset
2. Giải nén tệp vừa tải về và đưa thư mục `DryBeanDataset` vào đúng đường dẫn `data/raw/` trong dự án:
   ```text
   DA14-DryBean/
   └── data/
       └── raw/
           └── DryBeanDataset/
               ├── Dry_Bean_Dataset.arff
               └── Dry_Bean_Dataset.xlsx
   ```

---

## 2. Cài đặt môi trường ảo (Dành cho thành viên mới clone dự án)

1. Tại thư mục gốc của dự án, nháy đúp chuột vào tệp **`setup.bat`** (hoặc chạy lệnh `.\setup.bat` trong Terminal) để hệ thống tự động tạo môi trường ảo `.venv` và cài đặt toàn bộ thư viện trong `requirements.txt`.
2. Mở thư mục dự án bằng **VS Code**, nhấn tổ hợp phím **`Ctrl + Shift + P`** -> gõ **`Python: Select Interpreter`**.
3. Chọn dòng có đường dẫn **`.\.venv\Scripts\python.exe`** để kích hoạt môi trường ảo.
4. Mở Terminal mới trong VS Code (`Ctrl + ~`), đảm bảo thấy chữ `(.venv)` xuất hiện ở đầu dòng lệnh trước khi chạy code.

---

## 3. Quy trình chạy từng bước

### Bước 1: Nạp dữ liệu và kiểm kê trung thực

Chạy lệnh sau tại thư mục gốc `DA14-DryBean`:

```powershell
python data/nap.py
```

- **Kết quả đầu ra:**
  - Terminal hiển thị đầy đủ 7 thông số kiểm kê (xác nhận cột `Class`, tách 16 đặc trưng số, bảng `Min–Max`, kiểu dữ liệu, số ô khuyết, số bản ghi trùng lặp, phân bố lớp và đối chiếu số liệu với đề tài).
  - Tự động sinh tệp báo cáo: `bao_cao/Bao_Cao_DA14_DryBean_Buoc1.md`.

### Bước 2: Khám phá và trực quan hóa dữ liệu (EDA)

Chạy lệnh sau tại thư mục gốc `DA14-DryBean`:

```powershell
python analysis/kham_pha.py
```

- **Kết quả đầu ra:**
  - Tự động xuất **6 biểu đồ** (thuộc 6 loại trực quan hóa khác nhau) lưu vào thư mục `results/hinh/`:
    1. `hinh_01_heatmap_tuong_quan.png` (Bản đồ nhiệt tương quan $16 \times 16$)
    2. `hinh_02_boxplot_kich_thuoc.png` (Biểu đồ hộp 4 đặc trưng kích thước theo 7 giống)
    3. `hinh_03_scatter_area_perimeter.png` (Biểu đồ phân tán Diện tích theo Chu vi)
    4. `hinh_04_phuong_sai_tich_luy_pca.png` (Đường phương sai giải thích tích lũy qua PCA)
    5. `hinh_05_bar_so_luong_giong_dau.png` (Biểu đồ cột số lượng hạt từng giống)
    6. `hinh_06_kde_ty_le_khung_hinh.png` (Đường cong mật độ xác suất tỷ lệ khung hình)
  - Lưu bảng liệt kê đủ 21 cặp đặc trưng có tương quan tuyệt đối $|r| > 0.9$ tại `results/bang/bang_21_cap_tuong_quan_tren_09.csv`.
  - Tự động sinh tệp báo cáo kèm nhận xét chi tiết cho từng biểu đồ: `bao_cao/Bao_Cao_DA14_DryBean_Buoc2.md`.

### Bước 3: Hướng dẫn mở Server và xem giao diện Web trên Localhost

Chạy lệnh ở dưới và kiểm tra trong folder result có file `da14_web_data.json` chưa. Lệnh này tự động gom dữ liệu thật và bảng thực nghiệm thành tệp **`results/da14_web_data.json`**

```
Xuất 1 tệp JSON duy nhất để hiển thị lên giao diện Web:

python app/export_json_web.py
```

Để xem kết quả trực quan trên giao diện web thực hiện theo 3 bước sau:

1. **Mở Terminal tại thư mục chứa mã nguồn Web (`da14_dry_bean_web`):**

   ```
   cd duong/dan/toi/da14_dry_bean_web
   ```

   *(Lưu ý: Mở Terminal ngay tại thư mục chứa tệp `index.html` của web).*
2. **Khởi chạy máy chủ cục bộ (Local Server) ở cổng `8080`:**

   ```
   python -m http.server 8080
   ```

   * Khi Terminal hiện dòng `Serving HTTP on :: port 8080 (http://[::]:8080/) ...` nghĩa là server đã bật thành công. **Giữ nguyên cửa sổ Terminal này, không tắt đi trong lúc xem web.**
3. **Mở trình duyệt và truy cập đường dẫn Localhost:**

   * Mở Chrome, Edge hoặc Brave và nhập vào thanh địa chỉ:

```
	http://localhost:8080
```

* *(Nếu bạn bật server ở thư mục cha bên ngoài, hãy bấm vào thư mục `da14_dry_bean_web/` hiển thị trên màn hình hoặc truy cập `http://localhost:8080/da14_dry_bean_web/`).*

4. **Nạp dữ liệu thật của nhóm lên Web:**
   * Trên thanh công cụ góc trên bên phải của trang web, bấm nút  **`results/ JSON`** .
   * Chọn tệp **`da14_web_data.json`**  -> giao diện sẽ cập nhật ngay toàn bộ biểu đồ và bảng số liệu thật của nhóm.
   * Khi xem xong, quay lại cửa sổ Terminal và nhấn **`Ctrl + C`** để tắt server.

## 4. Lưu ý khi làm việc nhóm trên Git

- Các tệp báo cáo tự động sinh ra trong `bao_cao/` và hình ảnh trong `results/hinh/` đã được cấu hình bỏ qua trong `.gitignore` (chỉ giữ lại thư mục thông qua `.gitkeep`).
- Thành viên nhóm sau khi `git pull` chỉ cần chạy lại các lệnh ở **Mục 4** để tái tạo đầy đủ hình ảnh và báo cáo trên máy cá nhân mà không gây xung đột mã nguồn (merge conflict).

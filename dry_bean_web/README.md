# DA14 · Dry Bean Lab — Tâm hay medoid: hai cách chọn đại diện cho một cụm

Ứng dụng web tương tác minh họa đồ án phân tích dữ liệu khám phá (EDA), giảm chiều (PCA) và phân cụm (K-Means vs K-Medoids) trên tập dữ liệu **13.611 hạt đậu khô (Dry Bean)**.

## Cấu trúc thư mục dự án

```text
da14_dry_bean_web/
├── index.html                # Khung cấu trúc HTML của 6 màn hình & Modal Data Adapter
├── css/
│   ├── tokens.css            # Hệ thống biến màu pastel, font chữ, viền & reset CSS
│   ├── layout.css            # Thanh điều hướng Topbar, Workbench 3 cột & Responsive
│   └── components.css        # Thẻ KPI, nút bấm, thanh trượt, bảng dữ liệu, Canvas & Modal
├── js/
│   ├── constants.js          # Hằng số 7 giống đậu, 16 đặc trưng, phương sai PCA & kịch bản 6 bước
│   ├── state.js              # Quản lý trạng thái ứng dụng tập trung (state)
│   ├── data.js               # Sinh dữ liệu 13.611 hạt & xử lý tiêm ngoại lai 1% / chuẩn hóa
│   ├── algorithms.js         # Thuật toán K-Means++, K-Medoids (PAM), chỉ số ARI & Silhouette
│   ├── canvas-scatter.js     # Vẽ 2 bản đồ phân tán chia đôi, đồng bộ Zoom/Pan & chọn Medoid
│   ├── canvas-charts.js      # Đồ thị 3 đường theo k, Boxplot EDA, Scree PCA & mô phỏng Màn 04
│   ├── ui.js                 # Cập nhật KPI, Inspector 16 số đo, bảng B8 & Adapter nạp JSON
│   └── main.js               # Điểm khởi chạy DOMContentLoaded và gắn sự kiện điều khiển
└── README.md                 # Tài liệu hướng dẫn cấu trúc
```

## Cách chạy

1. Giải nén thư mục `da14_dry_bean_web/`.
2. Mở trực tiếp tệp `index.html` bằng trình duyệt (Chrome, Edge, Brave) hoặc chạy qua máy chủ tĩnh:
   ```bash
   python -m http.server 8080
   ```
3. Khi hoàn thiện phần xử lý Python ở thư mục `results/`, bấm nút **results/ JSON** trên thanh góc phải để nạp trực tiếp tệp kết quả thật vào giao diện.

/**
 * =========================================================================
 * dry_bean_animation/js/story.js
 * Kịch bản chậm (~126 giây ở 1×) giải thích rất kỹ theo LÝ THUYẾT & theo CODE
 * =========================================================================
 */
window.ANIM_STORY = [
  {
    id: 1,
    shortTitle: 'Số 0 → Dữ liệu thô',
    badge: 'CHƯƠNG 1 / 7 · KHỞI ĐIỂM TỪ CON SỐ 0',
    badgeBg: 'var(--blue-pastel)',
    start: 0.0,
    end: 16.0,
    title: 'Từ 0 hạt đến 13.611 hạt thô: Vì sao đơn vị đo làm máy bị "mù" hình dáng?',
    formula: 'd(x, y) = √( ΔArea² + ΔShapeFactor1² )  ≈  |ΔArea|  (do 254.616 ≫ 0,01)',
    mechanism: {
      input: '13.611 mẫu hạt đậu thật thuộc 7 giống, mỗi hạt có 16 đặc trưng hình học chưa đổi đơn vị.',
      process: 'Chiếu thẳng Area (px²) và AspectRation lên hệ trục thô để quan sát độ lệch phương sai.',
      output: 'Nếu phân cụm trực tiếp ở thang đo thô, ARI chỉ đạt 0,379 ± 0,011 (kém xa bản chuẩn hóa).'
    },
    theory: {
      heading: 'Nguyên lý toán học: Tính không bất biến thang đo của khoảng cách Euclid',
      points: [
        'Khoảng cách Euclid L₂(x, y) = √Σ(x_j − y_j)² cộng trực tiếp bình phương sai lệch của 16 cột mà không quan tâm đơn vị đo là pixel² hay tỷ số 0–1.',
        'Cột Area có phương sai Var(Area) ≈ 8,6×10⁸ (px⁴), trong khi Var(roundness) ≈ 0,0035 — tỷ lệ chênh lệch xấp xỉ 2,4×10¹¹ lần.',
        'Vì đóng góp của trục hình dáng gần như bằng 0, mọi thuật toán dựa trên khoảng cách đều thoái hóa thành việc cắt lát dọc theo mỗi biến Diện tích.'
      ],
      mathNote: 'Chuẩn bị chia tách Train/Test phân tầng 80/20 ngay từ đầu để bảo toàn phân phối 7 lớp (từ 522 Bombay đến 3.546 Dermason).'
    },
    codeExplain: {
      file: 'data/tien_xu_ly.py',
      func: 'chia_phan_tang() & chuan_bi(chuan_hoa=False)',
      snippet: `idx_tr, idx_te = train_test_split(
    idx_all, test_size=0.2, stratify=y_arr, random_state=seed
)
# Khi chuan_hoa=False (baseline thô):
Z_tr = X_tr.copy()  # Area (hàng trăm nghìn) áp đảo 15 cột còn lại`,
      steps: [
        'train_test_split(..., stratify=y_arr) khóa tỷ lệ 7 giống hạt giống nhau giữa tập Train (80%) và Test (20%).',
        'Khi đặt chuan_hoa=False trong chạy baseline (thuat_toan="kmeans_chua_chuan_hoa"), dữ liệu gốc đi thẳng vào kmeans() nên ARI tụt xuống ~0,379.'
      ]
    },
    bullets: [
      '0 → 13.611 hạt nạp theo đúng phân bố UCI Dry Bean (Dermason 3.546 nhiều gấp ~6,8 lần Bombay 522).',
      'Trục ngang kéo dài tới 254.616 px², trục dọc bị ép thành một dải mỏng manh.',
      'Ô đánh giá bên phải đang ghim mốc Baseline thô (ARI = 0,379) để đối chiếu cho các chương sau.'
    ],
    getPhaseInfo: (u) => {
      if (u < 0.42) {
        return {
          tag: 'Nhịp 1 / 3 · Nạp dữ liệu từ số 0',
          caption: 'Bắt đầu từ tập rỗng (0 hạt): máy đọc tuần tự từng mẫu hạt chụp chuẩn hóa từ giống nhỏ Dermason tới giống lớn Bombay cho đến khi đủ toàn bộ 13.611 hạt.'
        };
      }
      if (u < 0.72) {
        return {
          tag: 'Nhịp 2 / 3 · Soi chênh lệch hàng chục nghìn lần',
          caption: 'Trên trục tọa độ thô, trục ngang Area trải tới 254.616 px², ép dẹt toàn bộ trục hình dáng AspectRation (1,0 → 2,4) thành một vệt mảnh ở đáy.'
        };
      }
      return {
        tag: 'Nhịp 3 / 3 · Kết quả đo lường khi chưa chuẩn hóa',
        caption: 'Thử chạy K-Means ngay trên số thô cho kết quả ARI = 0,379 (dù Silhouette hình học cao giả tạo = 0,533 vì chỉ chia cụm theo cỡ Area!).'
      };
    }
  },
  {
    id: 2,
    shortTitle: 'Chuẩn hóa Z-score',
    badge: 'CHƯƠNG 2 / 7 · CHUẨN HÓA Z-SCORE',
    badgeBg: 'var(--mint)',
    start: 16.0,
    end: 30.0,
    title: 'Chuẩn hóa Z-score: Đưa 16 thông số khác đơn vị về chung thước đo σ (chống rò rỉ)',
    formula: 'Z_j = (X_j − μ_train,j) / σ_train,j   ⇒   E[Z_j] = 0,  Var(Z_j) = 1',
    mechanism: {
      input: '16 đặc trưng có độ lớn lệch pha tới hàng chục triệu lần về phương sai.',
      process: 'Khớp μ, σ trên đúng tập Train 80% rồi chuẩn hóa Z-score đồng loạt cho cả 16 biến.',
      output: 'Cân bằng quyền biểu quyết: ±1σ của Độ tròn có trọng số ngang ±1σ của Diện tích.'
    },
    theory: {
      heading: 'Nguyên lý toán học: Biến đổi Affine giữ dạng phân phối & Anti-Leakage',
      points: [
        'Phép trừ μ_train dịch chuyển gốc tọa độ về đúng trọng tâm đám mây dữ liệu (mean centering).',
        'Phép chia σ_train thu gọn các biến biên độ lớn (Area) và phóng đại biến biên độ nhỏ (ShapeFactor1..4) để mọi phương sai đều chuẩn bằng 1.',
        'Bắt buộc chỉ khớp μ, σ trên X_tr (tập huấn luyện): nếu dùng chung trung bình của toàn bộ 13.611 dòng trước khi chia tách sẽ gây rò rỉ thông tin (data leakage) từ tập kiểm tra.'
      ],
      mathNote: 'Chuẩn hóa Z-score giữ nguyên thứ tự xếp hạng trong từng cột nhưng thay đổi hoàn toàn hình học khoảng cách giữa các điểm đa chiều.'
    },
    codeExplain: {
      file: 'data/tien_xu_ly.py',
      func: 'khop_chuan_hoa() & ap_chuan_hoa()',
      snippet: `scaler = khop_chuan_hoa(X_tr)   # StandardScaler().fit(X_tr) — chỉ tính trên Train
Z_tr = ap_chuan_hoa(scaler, X_tr) # (X_tr - scaler.mean_) / scaler.scale_
Z_te = ap_chuan_hoa(scaler, X_te) # Dùng chính μ, σ của Train cho Test`,
      steps: [
        'Hàm chia_phan_tang() tách 80% Train trước khi bất kỳ phép thống kê nào được tính toán.',
        'StandardScaler().fit(X_tr) lưu lại vector 16 giá trị trung bình (mean_) và 16 độ lệch chuẩn (scale_) rồi biến đổi cho cả Z_tr lẫn Z_te.'
      ]
    },
    bullets: [
      'Nhịp 1: Trừ μ_train dời tâm toàn bộ 13.611 hạt về gốc 0.',
      'Nhịp 2: Chia σ_train kéo giãn trục dọc hình dáng ngang bằng trục ngang diện tích.',
      'Nhịp 3: Khóa chặt μ, σ theo tập Train để tái lập sạch cho toàn bộ thử nghiệm sau.'
    ],
    getPhaseInfo: (u) => {
      if (u < 0.30) {
        return {
          tag: 'Nhịp 1 / 3 · Tịnh tiến về gốc tọa độ (X − μ_train)',
          caption: 'Lấy từng số đo trừ đi trung bình của cột tương ứng trên tập Train (ví dụ trừ ~53.046 px² ở cột Area) để tâm phân bố rơi đúng vào điểm 0.'
        };
      }
      if (u < 0.72) {
        return {
          tag: 'Nhịp 2 / 3 · Thu phóng về chung độ lệch chuẩn (/ σ_train)',
          caption: 'Quan sát đám mây điểm bung nở theo chiều dọc! Các đặc trưng hình dáng thuôn/tròn trước đây bị bóp nghẹt nay mở rộng cân đối trong vùng [-3σ, +3σ].'
        };
      }
      return {
        tag: 'Nhịp 3 / 3 · Chuẩn bị đầu vào sạch cho PCA & Phân cụm',
        caption: 'Khi 16 cột cùng mang đơn vị độ lệch chuẩn σ, hai giống có diện tích gần nhau như Cali và Barbunya đã có thể tách nhau dựa vào hình dáng vỏ hạt.'
      };
    }
  },
  {
    id: 3,
    shortTitle: 'Nén chiều PCA',
    badge: 'CHƯƠNG 3 / 7 · GIẢM CHIỀU PCA QUA SVD',
    badgeBg: 'var(--lavender)',
    start: 30.0,
    end: 46.0,
    title: 'Cơ chế PCA qua phân rã SVD: Gộp 21 cặp biến dư thừa về mặt phẳng PC1–PC2',
    formula: 'Z_c = U Σ Vᵀ  ⇒  Z_d = (Z − μ_pca) · (Vᵀ[:d])ᵀ   |   λ_j = σ_j² / (n − 1)',
    mechanism: {
      input: 'Ma trận 16 chiều Z_tr có 21/120 cặp tương quan |r| > 0,9 (cond(Z) = 2.229,88).',
      process: 'Phân rã SVD tìm hệ trục trực giao mới tối đa hóa phương sai giữ lại, chuẩn hóa dấu trục ổn định.',
      output: '2D giữ 81,9% để quan sát; 4D giữ 95,0%; 7D đạt 99,6% (đỉnh ARI của PAM).'
    },
    theory: {
      heading: 'Nguyên lý toán học: Phân rã Giá trị Kỳ dị SVD & Phương sai Tích lũy',
      points: [
        'Thay vì tính ma trận hiệp phương sai Cov = ZᵀZ/(n−1) dễ khuếch đại sai số làm tròn (cond(Cov) ≈ 4,97×10⁶), PCA ổn định số học dùng trực tiếp SVD trên ma trận đã trừ trung bình: Z_c = U Σ Vᵀ.',
        'Mỗi hàng của Vᵀ là một trục chính (vector riêng trực giao từng đôi một): PC1 (55,47%) tải dương mạnh từ Area, ConvexArea, Perimeter (trục Kích thước); PC2 (26,43%) tải dương AspectRation, đối lập âm Compactness/roundness (trục Hình dáng).',
        'Tỉ lệ thông tin giữ được bằng tổng λ₁..λ_d chia tổng Σλ: d=2 đạt 81,9%, d=4 đạt 95,0%, d=7 đạt 99,6%.'
      ],
      mathNote: 'Chuẩn hóa dấu trục (max_abs element của mỗi hàng Vᵀ > 0) giúp kết quả chiếu giống hệt giữa các máy và thư viện.'
    },
    codeExplain: {
      file: 'models/pca.py',
      func: 'khop_pca() & chieu()',
      snippet: `Zc = Z - mean
U, S, Vt = np.linalg.svd(Zc, full_matrices=False)
_, Vt = _chuan_hoa_dau_svd(U, Vt)     # Khóa dấu ổn định
ty_le = (S ** 2 / (n - 1)) / np.sum(S ** 2 / (n - 1))
# Chiếu xuống d chiều:
Z_d = (X_arr - mo_hinh["mean"]) @ Vt[:d].T`,
      steps: [
        'khop_pca(Z_tr) tự viết 100% bằng NumPy np.linalg.svd, không dùng sklearn.decomposition.PCA ở tầng lõi thuật toán.',
        '_chuan_hoa_dau_svd đảo dấu cặp vector kỳ dị sao cho thành phần có trị tuyệt đối lớn nhất luôn dương, bảo đảm tái lập 100% và khớp sklearn trong test.'
      ]
    },
    bullets: [
      'Area & ConvexArea tương quan r = 0,9999; Compactness & ShapeFactor3 tương quan r = 0,9987.',
      'Mặt phẳng PC1–PC2 giúp mắt người thấy toàn cảnh 7 giống đậu dù chỉ dùng 2 trục trên màn hình.',
      'Khi phân cụm, ta đối chiếu cả d=2 (81,9%), d=4 (95,0%) và không gian gốc d=16.'
    ],
    getPhaseInfo: (u) => {
      if (u < 0.35) {
        return {
          tag: 'Nhịp 1 / 3 · Tại sao 16 cột lại nén được xuống ít chiều như vậy?',
          caption: 'Trong 16 số đo, nhóm kích thước (Diện tích, Chu vi, Bao lồi, Đường kính) đo cùng một tính chất vật lý với hệ số tương quan |r| > 0,95. PCA tìm cách gộp chúng thành 1 trục duy nhất.'
        };
      }
      if (u < 0.72) {
        return {
          tag: 'Nhịp 2 / 3 · Xoay trục trực giao PC1 (Cỡ) & PC2 (Dáng)',
          caption: 'Từng điểm hạt đang xoay mượt sang hệ trục SVD: các hạt to nặng (Bombay) xếp về bên phải (+PC1), hạt dài (Horoz) ở trên (+PC2) còn hạt tròn (Seker) nằm dưới (-PC2).'
        };
      }
      return {
        tag: 'Nhịp 3 / 3 · 4 mốc ngưỡng phương sai trong code Python (k_giu)',
        caption: 'Hàm k_giu() đo chính xác: giữ 80% cần 2 trục (81,9%), giữ 90% và 95% đều cần 4 trục (95,0%), giữ 99% cần 7 trục (99,6%) trước khi đánh giá đủ 16D.'
      };
    }
  },
  {
    id: 4,
    shortTitle: 'Vòng lặp K-Means',
    badge: 'CHƯƠNG 4 / 7 · CƠ CHẾ K-MEANS++ (LLOYD)',
    badgeBg: 'var(--blue-pastel)',
    start: 46.0,
    end: 68.0,
    title: 'Cơ chế K-Means++: Khởi tạo D², Gán nhãn Euclid & Cập nhật Tâm trung bình cộng (+)',
    formula: 'SSE = Σ_c Σ_{i ∈ C_c} ||x_i − μ_c||₂²   ·   μ_c = (1/|C_c|) Σ x_i  (điểm ảo!)',
    mechanism: {
      input: '13.611 điểm 16D đã chuẩn hóa, số cụm k = 7.',
      process: 'K-Means++ rải tâm theo phân phối D² → Lặp (1) Gán nhãn gan_cum() + (2) Tính trung bình cap_nhat_tam().',
      output: 'Tổng bình phương sai số SSE giảm đơn điệu qua 12 vòng lặp; ARI đạt 0,668, NMI đạt ~0,71.'
    },
    theory: {
      heading: 'Nguyên lý toán học: Thuật toán EM / Lloyd giảm dần hàm mục tiêu L2 (SSE)',
      points: [
        'Khởi tạo K-Means++: chọn hạt đầu đều ngẫu nhiên; tâm thứ c chọn điểm x với xác suất P(x) = D²(x) / ΣD²(y), giúp các tâm ban đầu phủ đều 7 giống thay vì chụm lại 1 vùng.',
        'Bước Gán (E-step): cố định tập tâm μ, gán mỗi điểm vào cụm c gần nhất theo khoảng cách bình phương → chắc chắn không làm SSE tăng.',
        'Bước Cập nhật (M-step): với cố định phân hoạch C_c, đạo hàm ∂SSE/∂μ_c = 0 cho nghiệm duy nhất là TRUNG BÌNH CỘNG μ_c = mean(C_c) → SSE giảm nghiêm ngặt cho tới cực tiểu địa phương. Tuy nhiên μ_c chỉ là tọa độ ảo, không trùng hạt thật!'
      ],
      mathNote: 'Vì chọn hàm mục tiêu L2 (bình phương), một điểm sai lệch gấp r lần đóng góp r² lần vào vị trí trung bình μ_c.'
    },
    codeExplain: {
      file: 'models/kmeans.py',
      func: 'kmeanspp(), gan_cum(), cap_nhat_tam(), kmeans()',
      snippet: `tam = kmeanspp(X_arr, k, rng)         # Chọn xác suất D² (d2_min)
for it in range(1, max_iter + 1):
    nhan, d2_min = gan_cum(X_arr, tam) # Gán nhãn bằng gan_gan_nhat theo khối
    sse = float(np.sum(d2_min))        # Ghi vào lich_su_sse (luôn giảm)
    tam_moi = cap_nhat_tam(X_arr, nhan, k, tam, rng) # X_arr[nhan==c].mean(axis=0)`,
      steps: [
        'gan_cum() gọi gan_gan_nhat() chia khối (chunk 4096) để tính khoảng cách không tràn RAM khi n = 13.611.',
        'cap_nhat_tam() lấy .mean(axis=0) của từng cụm; nếu cụm bị rỗng, tự động lấy hạt xa tâm hiện tại nhất để cứu cụm.'
      ]
    },
    bullets: [
      'Theo dõi ô SSE (Mục tiêu L2) ở bảng bên phải: SSE giảm đều từ Vòng 0 đến Vòng 12.',
      'Các vệt nét đứt xanh thể hiện quỹ đạo trượt của 7 tâm trung bình cộng (+) qua từng vòng.',
      'Dấu (+) rơi vào khoảng trống giữa đám mây — không phải một hạt đậu thực tế nào.'
    ],
    getPhaseInfo: (u) => {
      if (u < 0.22) {
        return {
          tag: 'Nhịp 1 / 4 · Vòng 0: Khởi tạo kmeanspp() rải tâm theo D²',
          caption: 'Hàm kmeanspp() chọn tâm đầu ngẫu nhiên, sau đó tính bình phương khoảng cách d2_min và dùng tìm kiếm nhị phân np.searchsorted trên tổng tích lũy D² để chọn các tâm tiếp theo ở thật xa nhau (ARI = 0,444).'
        };
      }
      if (u < 0.56) {
        return {
          tag: 'Nhịp 2 / 4 · Vòng 1 → 6: Luân phiên gan_cum() và cap_nhat_tam()',
          caption: 'Hãy xem hai số ở cột phải chạy cùng lúc: SSE (tổng bình phương sai số) tụt nhanh qua từng vòng lặp trong khi ARI tăng vọt 0,444 → 0,661 khi các dấu (+) trượt vào giữa 7 cụm.'
        };
      }
      if (u < 0.84) {
        return {
          tag: 'Nhịp 3 / 4 · Vòng 7 → 12: Tiệm cận tol_hieu_dung và dừng hội tụ',
          caption: 'Khi độ dịch chuyển giữa tam_moi và tam cũ nhỏ hơn ngưỡng tol_hieu_dung (hoặc nhãn không đổi nữa), vòng lặp thoát ra. Toàn tập hội tụ ở ARI = 0,668.'
        };
      }
      return {
        tag: 'Nhịp 4 / 4 · Hạn chế của Tâm ảo (+): Không chỉ ra được hạt mẫu thật',
        caption: 'Vì cap_nhat_tam() dùng X_arr[mask].mean(axis=0), dấu (+) chỉ là vector trung bình 16 số thực — người kiểm định chất lượng không thể nhặt được "hạt đậu trung bình" đó ngoài đời thực.'
      };
    }
  },
  {
    id: 5,
    shortTitle: 'Song song Medoid PAM',
    badge: 'CHƯƠNG 5 / 7 · CƠ CHẾ K-MEDOIDS (PAM)',
    badgeBg: 'var(--mint)',
    start: 68.0,
    end: 90.0,
    title: 'Cơ chế K-Medoids PAM (BUILD + SWAP): Cách thuật toán tìm ra 7 "Hạt mẫu thật" (◉)',
    formula: 'TD = Σ_{i=1..n} min_{m ∈ M} d(x_i, m)   với M ⊂ X  (|M| = k, m phải là hạt thật!)',
    mechanism: {
      input: 'Ma trận khoảng cách Euclid D giữa các điểm mẫu thật (xây theo khối để tiết kiệm RAM).',
      process: 'Pha BUILD chọn tham lam giảm chi phí sâu nhất → Pha SWAP tính độ lợi vector hóa O(k·n²) hoán đổi tốt nhất.',
      output: 'Đạt ARI = 0,711 (vượt K-Means 0,668) và cung cấp đủ 16 số đo thật của từng medoid ◉.'
    },
    theory: {
      heading: 'Nguyên lý toán học: Tối ưu rời rạc trên không gian hạt thật (BUILD & SWAP)',
      points: [
        'Khác K-Means cập nhật liên tục bằng đạo hàm trung bình, PAM giải bài toán chọn tổ hợp rời rạc k điểm từ chính tập X nhằm cực tiểu tổng khoảng cách L1/tuyến tính TD = Σ d(x_i, medoid gần nhất).',
        'Pha BUILD: chọn m₀ = argmin Σ D[:, i] (điểm trung tâm nhất). Ở bước kế, mỗi ứng viên i thu về độ lợi Σ max(d_gan_nhat[j] − D[j, i], 0) — chọn ứng viên giảm TD nhiều nhất.',
        'Pha SWAP: mỗi vòng xét tất cả cặp (medoid m_r, phi-medoid h). Dùng 2 giá trị d₁ (tới medoid gần 1) và d₂ (gần 2) để tính nhanh ΔTD(r, h) trong O(k·n²); chỉ hoán đổi nếu ΔTD < 0 (đảm bảo tổng chi phí L1 giảm nghiêm ngặt).'
      ],
      mathNote: 'Vì chi phí tuyến tính không bình phương và mỗi m_c bắt buộc là 1 điểm có thật, hình học cụm ôm sát phân phối thực tế của 7 giống.'
    },
    codeExplain: {
      file: 'models/pam.py',
      func: 'build(), swap(), pam(), gan_medoid()',
      snippet: `# 1. Pha BUILD (models/pam.py):
m0 = int(np.argmin(D_arr.sum(axis=1)))  # Hạt nằm giữa toàn tập nhất
do_loi = np.maximum(d_gan_nhat[:, None] - D_arr, 0.0).sum(axis=0)
# 2. Pha SWAP vector hóa + gán toàn tập:
nhan = gan_medoid(space, space[medoid_global]) # Chiếu ra 13.611 hạt`,
      steps: [
        'chi_phi(D, medoid) trả về D[:, medoid].min(axis=1).sum() — tổng khoảng cách tuyến tính giảm qua từng bước swap().',
        'Trong thí nghiệm thật (experiments/chay.py), chạy PAM trên tập mẫu con n_mau=3000 bằng D_sub đối xứng (68,7 MB) rồi gan_medoid() gán toàn bộ tập train.'
      ]
    },
    bullets: [
      'Theo dõi cột phải: tổng khoảng cách L1 (chi_phi) giảm từ Khởi tạo thô → Pha BUILD (ARI 0,697) → Pha SWAP (ARI 0,711).',
      'K-Medoids đồng thời cao hơn K-Means ở cả chỉ số ARI, NMI lẫn Độ tinh khiết cụm (Purity %).',
      'Hạt M7 (#Bean_00... · BOMBAY) được đánh dấu sáng để đối chiếu trực tiếp 16 số đo thực tế.'
    ],
    getPhaseInfo: (u) => {
      if (u < 0.30) {
        return {
          tag: 'Nhịp 1 / 3 · Pha BUILD (build()): Chọn dần các hạt trung tâm thật',
          caption: 'Bên phải, hàm build() tìm hạt có tổng khoảng cách tới toàn tập nhỏ nhất làm gốc m₀, rồi chọn tham lam thêm 6 hạt có độ lợi max(d_gan_nhat − D[j, i], 0) cao nhất → ARI lập tức nhảy từ 0,443 lên 0,697!'
        };
      }
      if (u < 0.68) {
        return {
          tag: 'Nhịp 2 / 3 · Pha SWAP (swap()): Hoán đổi từng cặp để tối ưu rời rạc',
          caption: 'Hàm swap() kiểm tra mọi phép thế (m_r ↔ h) bằng công thức d₁, d₂ tìm ra bước giảm chi phí TD sâu nhất → tinh chỉnh vị trí các hạt ◉ đưa ARI đạt đỉnh 0,711 và Purity lên ~79%.'
        };
      }
      return {
        tag: 'Nhịp 3 / 3 · Soi hồ sơ hạt mẫu BOMBAY (◉ M7) ngay trên thực địa',
        caption: 'Vì m_c ∈ X thật, ta tra ngược chỉ số medoid_global để đọc chính xác Diện tích, Chu vi, Tỉ lệ dài/rộng, Độ tròn của đúng 1 hạt đậu mẫu đặt cạnh dây chuyền phân loại.'
      };
    }
  },
  {
    id: 6,
    shortTitle: 'Sốc Ngoại lai 1%',
    badge: 'CHƯƠNG 6 / 7 · BẢN CHẤT KHÁNG NHIỄU L2 VS L1',
    badgeBg: 'var(--coral)',
    start: 90.0,
    end: 110.0,
    title: 'Giải thích triệt để: Vì sao 1% ngoại lai (×10,5) bẻ gãy tâm K-Means (+) nhưng bất lực trước PAM (◉)',
    formula: 'Gradient MSE ∝ 2(x_out − μ)  →  ∞  |  Điểm gãy (Breakdown Point): Mean = 1/n, Medoid ≈ 50%',
    mechanism: {
      input: 'Tiêm nhiễu theo đúng hàm tiem_ngoai_lai(): giữ 99% hạt, chọn 1% (~136 hạt) nhân cột Area lên ×8..12 lần.',
      process: 'Bên trái: K-Means++ dời (+) theo trung bình cộng D². Bên phải: PAM kiểm tra ΔTD nếu dời ◉ sang hạt đỏ.',
      output: 'SSE K-Means vọt tăng & tâm lệch 16,55 σ (ARI tụt 0,668 → 0,538); PAM giữ nguyên hạt ◉ (ARI = 0,709).'
    },
    theory: {
      heading: 'Nguyên lý toán học: Điểm gãy thống kê (Breakdown Point) & Trực giác Đòn bẩy',
      points: [
        'Trung bình số học μ (K-Means) có Breakdown Point = 1/n (0% tiệm cận): chỉ 1 điểm văng ra vô cực cũng đủ kéo tâm μ trôi theo ra vô cực bất kể cụm có bao nhiêu hạt thật.',
        'Ngoài ra, trong khởi tạo K-Means++ (P ∝ D²), một hạt ngoại lai ở khoảng cách +25σ đóng góp D² = 625 lần so với hạt bình thường → gần như chắc chắn cướp mất 1 tâm khởi tạo, khiến 2 giống đậu thật bị ép gộp chung!',
        'Trái lại, hàm mục tiêu tuyến tính Σ d của K-Medoids giống khái niệm Trung vị đa chiều (Geometric Median / Breakdown Point cao): hoán đổi sang điểm xa cách +25σ làm tổng khoảng cách tới ~1.800 hạt bình thường tăng thêm ≈ +45.000 đơn vị nên hàm swap() lập tức loại bỏ.'
      ],
      mathNote: 'Trên toàn bộ 13.611 hạt thật ở đây: độ lệch tâm K-Means lên tới 16,55 σ (ARI -0,130), trong khi PAM chỉ biến thiên -0,002!'
    },
    codeExplain: {
      file: 'data/tien_xu_ly.py & experiments/chay.py',
      func: 'tiem_ngoai_lai(ty_le=0.01, he_so=(8.0, 12.0), cot="Area")',
      snippet: `X_moi = np.array(X_tr, copy=True)
X_moi[idx, col_idx] *= rng.uniform(8.0, 12.0, size=so_luong)
# Phải khớp scaler & PCA SẠCH trước đó (không fit lại trên dữ liệu nhiễm!)
Z_nhieu = ap_chuan_hoa(scaler_sach, X_moi)`,
      steps: [
        'tiem_ngoai_lai() chỉ sửa bản sao thô trên đúng cột "Area" (1% = 136 hạt) rồi dùng chính scaler và mô hình PCA sạch trước đó để chiếu (chống rò rỉ tham số).',
        'Trong K-Means, 136 hạt nhân ×10,5 Area biến thành vector có Z_Area ≈ +18σ khiến gan_cum() + cap_nhat_tam() kéo tâm lệch hoàn toàn trên không gian 16D.'
      ]
    },
    bullets: [
      'Nhìn ô SSE vs L1 Cost & Độ lệch tâm (+) bên phải: SSE bùng nổ còn đường đỏ nối tâm cũ → mới dài tới 16,55 σ.',
      'Chú ý NMI, Purity và ARI của K-Means đều đồng loạt sụp xuống màu đỏ báo động.',
      'Bên phải: K-Medoids PAM xanh an toàn — hầu như mọi chỉ số đều bám sát mốc dữ liệu sạch!'
    ],
    getPhaseInfo: (u) => {
      if (u < 0.28) {
        return {
          tag: 'Nhịp 1 / 3 · Giai đoạn tiem_ngoai_lai(): 1% hạt phóng đại ×10,5 lần',
          caption: 'Hàm tiem_ngoai_lai() nhân cột Area của 136 hạt mẫu lên ×10,5 rồi chiếu qua StandardScaler sạch ban đầu. Nhìn 136 đốm đỏ lao vọt sang cực phải mặt phẳng PCA!'
        };
      }
      if (u < 0.72) {
        return {
          tag: 'Nhịp 2 / 3 · Hiệu ứng đòn bẩy D² kéo tâm K-Means (+) văng 16,55 σ',
          caption: 'Vì kmeanspp() chọn theo D² và cap_nhat_tam() lấy trung bình cộng, 1 tâm K-Means bị hút vào đám ngoại lai (C7 văng phải →) làm xô lệch toàn bộ phân hoạch: ARI rớt 0,668 → 0,538, Độ lệch tâm đạt 16,55 σ!'
        };
      }
      return {
        tag: 'Nhịp 3 / 3 · Cơ chế bảo vệ tự nhiên của swap() trong PAM (ARI = 0,709)',
        caption: 'Hàm swap() thử dời medoid sang một hạt đỏ nhưng chi_phi tổng khoảng cách lập tức phình to do gần 2.000 hạt bình thường kéo lại. Kết quả PAM giữ chặt hạt mẫu thật ở ARI = 0,709!'
      };
    }
  },
  {
    id: 7,
    shortTitle: 'Hoàn chỉnh 10-seed',
    badge: 'CHƯƠNG 7 / 7 · TỔNG HỢP 10-SEED & MỞ RỘNG A',
    badgeBg: 'var(--yellow)',
    start: 110.0,
    end: 126.0,
    title: 'Hoàn chỉnh bài: Kiểm định Wilcoxon 10 seeds, Mốc đối chứng & Thất bại lý thú của Mahalanobis',
    formula: 'Wilcoxon p = 0,00195 (< 0,05)  ·  Mahalanobis d_M = √((x−y)ᵀ S⁻¹ (x−y))  [cond > 10⁴ từ d = 12]',
    mechanism: {
      input: 'Tổng hợp chạy tự động trên 10 seeds (n = 3.000/seed) với mọi thuật toán, d ∈ {2, 4, 16}, k ∈ [2..10].',
      process: 'Kiểm định phi tham số Wilcoxon bắt cặp theo seed + đối chiếu Random Forest + thử làm trắng Mahalanobis SVD.',
      output: 'Hoàn chỉnh bức tranh thực nghiệm: PAM thắng ở 16D sạch & nhiễu; chỉ rõ khi nào Mahalanobis phản tác dụng.'
    },
    theory: {
      heading: 'Nguyên lý toán học: Kiểm định Wilcoxon bắt cặp & Suy biến nghịch đảo Ma trận Hiệp phương sai',
      points: [
        'Wilcoxon Signed-Rank bắt cặp trên cùng 10 seed kiểm tra giả thuyết H₀ (chênh lệch = 0) mà không cần giả định phân phối chuẩn: p = 0,00195 < 0,05 khẳng định PAM hơn K-Means ở d = 16 là có ý nghĩa thống kê thực sự.',
        'Ở Mở rộng A, khoảng cách Mahalanobis chuẩn hóa theo S⁻¹ = WᵀW (làm trắng dữ liệu XWᵀ để khử tương quan).',
        'Tuy nhiên vì tập Dry Bean có 21 cặp đa cộng tuyến cực mạnh, trị kỳ dị nhỏ nhất s_min tụt về ~1,7×10⁻⁶ ở d = 16 (cond(Cov_d) = 30.738 > 10⁴ ngay từ d = 12 → 5,08×10⁶ ở d = 16). Nghịch đảo 1/s_min thổi phồng nhiễu siêu nhỏ làm vỡ cấu trúc cụm (ARI tụt còn 0,489; Tikhonov cứu lên 0,555 vẫn dưới Euclid 0,695).'
      ],
      mathNote: 'Đây là phát hiện quan trọng: khử tương quan toàn cục kiểu Mahalanobis gây hại khi dữ liệu đa cộng tuyến cực mạnh và hình dáng các lớp không đồng nhất.'
    },
    codeExplain: {
      file: 'experiments/chay.py & models/mahalanobis.py',
      func: 'kiem_dinh_wilcoxon(), nghich_dao_gia_svd(), phan_ra_mahalanobis()',
      snippet: `# 1. Kiểm định Wilcoxon (experiments/chay.py):
stat, p_val = wilcoxon(x_pam, y_km, zero_method="wilcox", alternative="two-sided")
# 2. Mở rộng A Mahalanobis SVD + Tikhonov (models/mahalanobis.py):
U, s, Vt = np.linalg.svd(S_sym, full_matrices=False)
s_inv[giu_mask] = 1.0 / (s[giu_mask] + float(tikonov))
W_lam_trang = np.sqrt(s_inv)[:, None] * Vt`,
      steps: [
        'kiem_dinh_wilcoxon() ghép cặp theo đúng 10 seed để xuất bảng kiem_dinh_wilcoxon.csv (p = 0,00195 cho cả ARI sạch và nhiễu tại d=16, k=7).',
        'nghich_dao_gia_svd() tính S_inv bằng phân rã SVD + điều chuẩn Tikhonov rồi biến đổi sang không gian làm trắng X @ W.T để tái sử dụng nguyên cụm hàm chạy PAM.'
      ]
    },
    bullets: [
      '10-seed Python (k=7, d=16): Sạch PAM 0,695 vs K-Means 0,665; Nhiễu 1% PAM 0,689 (-0,006) vs K-Means 0,598 (-0,067).',
      'Mốc đối chứng: Dummy (đoán DERMASON) đạt 26,04% (ARI = 0); Random Forest có giám sát đạt 92,03% (16D) và 92,88% (d=7).',
      'Mở rộng A: Giải thích định lượng đầy đủ vì sao Mahalanobis SVD (0,489) và Tikhonov (0,555) kém hơn Euclid chuẩn hóa (0,695).'
    ],
    getPhaseInfo: (u) => {
      if (u < 0.50) {
        return {
          tag: 'Nhịp 1 / 2 · Toàn bộ ô đánh giá nối thẳng vào Bảng 10-seed Wilcoxon',
          caption: 'Các chỉ số đánh giá vừa chạy (ARI, NMI, Silhouette, Purity, SSE/L1, Độ lệch tâm) khớp trực tiếp với xu hướng thống kê trên 10 lần chạy độc lập ở Python: PAM ổn định và vượt trội ở không gian 16D.'
        };
      }
      return {
        tag: 'Nhịp 2 / 2 · Hoàn chỉnh đồ án: Từ Dữ liệu thô → Lý thuyết → Code Python → Mở rộng',
        caption: 'Toàn bộ đồ án đã hoàn tất khép kín! Bạn có thể bấm nút bên trên để quay lại Phòng thí nghiệm Tương tác (index.html) hoặc dùng thanh tua bên dưới để xem lại bất kỳ nhịp nào.'
      };
    }
  }
];

window.ANIM_TOTAL_DURATION = window.ANIM_STORY[window.ANIM_STORY.length - 1].end;

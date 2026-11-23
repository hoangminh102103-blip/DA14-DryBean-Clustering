/**
 * =========================================================================
 * constants.js — HẰNG SỐ DỮ LIỆU DRY BEAN, KỊCH BẢN THÍ NGHIỆM & BẢNG SỐ LIỆU
 * =========================================================================
 */
const TOTAL_BEANS = 13611;

const VARIETIES = [
  { key: 'DERMASON', label: 'Dermason', count: 3546, color: '#2563EB', areaMean: 32118,  areaStd: 4100,  aspectMean: 1.49, aspectStd: 0.08, roundMean: 0.908, solidityMean: 0.988 },
  { key: 'SIRA',     label: 'Sira',     count: 2636, color: '#0D9488', areaMean: 44729,  areaStd: 4400,  aspectMean: 1.57, aspectStd: 0.09, roundMean: 0.884, solidityMean: 0.988 },
  { key: 'SEKER',    label: 'Seker',    count: 2027, color: '#D97706', areaMean: 39881,  areaStd: 4600,  aspectMean: 1.24, aspectStd: 0.06, roundMean: 0.944, solidityMean: 0.990 },
  { key: 'HOROZ',    label: 'Horoz',    count: 1928, color: '#E11D48', areaMean: 53648,  areaStd: 7100,  aspectMean: 2.02, aspectStd: 0.13, roundMean: 0.794, solidityMean: 0.985 },
  { key: 'CALI',     label: 'Cali',     count: 1630, color: '#7C3AED', areaMean: 75538,  areaStd: 8100,  aspectMean: 1.73, aspectStd: 0.11, roundMean: 0.845, solidityMean: 0.985 },
  { key: 'BARBUNYA', label: 'Barbunya', count: 1322, color: '#059669', areaMean: 69804,  areaStd: 9500,  aspectMean: 1.54, aspectStd: 0.12, roundMean: 0.800, solidityMean: 0.982 },
  { key: 'BOMBAY',   label: 'Bombay',   count: 522,  color: '#EA580C', areaMean: 173485, areaStd: 21000, aspectMean: 1.58, aspectStd: 0.11, roundMean: 0.864, solidityMean: 0.987 }
];

const CLUSTER_COLORS = [
  '#2563EB', '#0F766E', '#D97706', '#DC2626', '#7C3AED',
  '#0284C7', '#EA580C', '#4F46E5', '#65A30D', '#DB2777'
];

const FEATURE_META = [
  { key: 'Area',            group: 'Kích thước', unit: 'px²',   desc: 'Diện tích vùng hạt đậu tính bằng số điểm ảnh.' },
  { key: 'Perimeter',       group: 'Kích thước', unit: 'px',    desc: 'Chu vi đường biên bao quanh hạt đậu.' },
  { key: 'MajorAxisLength', group: 'Kích thước', unit: 'px',    desc: 'Chiều dài trục chính của elip ngoại tiếp hạt.' },
  { key: 'MinorAxisLength', group: 'Kích thước', unit: 'px',    desc: 'Chiều dài trục phụ vuông góc trục chính.' },
  { key: 'AspectRation',    group: 'Hình dáng',  unit: 'tỷ lệ', desc: 'Tỷ số trục chính / trục phụ (L / W).' },
  { key: 'Eccentricity',    group: 'Hình dáng',  unit: '0–1',   desc: 'Độ lệch tâm của elip tương đương.' },
  { key: 'ConvexArea',      group: 'Kích thước', unit: 'px²',   desc: 'Diện tích đa giác lồi nhỏ nhất bao trọn hạt.' },
  { key: 'EquivDiameter',   group: 'Kích thước', unit: 'px',    desc: 'Đường kính hình tròn có cùng diện tích.' },
  { key: 'Extent',          group: 'Hình dáng',  unit: 'tỷ lệ', desc: 'Tỷ số diện tích hạt trên khung chữ nhật bao.' },
  { key: 'Solidity',        group: 'Hình dáng',  unit: 'tỷ lệ', desc: 'Độ đặc của hạt: Area / ConvexArea.' },
  { key: 'roundness',       group: 'Hình dáng',  unit: '0–1',   desc: 'Độ tròn chuẩn hóa: 4π·Area / Perimeter².' },
  { key: 'Compactness',     group: 'Hình dáng',  unit: 'tỷ lệ', desc: 'Độ gọn: EquivDiameter / MajorAxisLength.' },
  { key: 'ShapeFactor1',    group: 'Hệ số SF',   unit: 'px⁻¹',  desc: 'Hệ số hình dạng 1: MajorAxisLength / Area.' },
  { key: 'ShapeFactor2',    group: 'Hệ số SF',   unit: 'px⁻¹',  desc: 'Hệ số hình dạng 2: MinorAxisLength / Area.' },
  { key: 'ShapeFactor3',    group: 'Hệ số SF',   unit: 'tỷ lệ', desc: 'Hệ số hình dạng 3: Area / ((Major/2)² · π).' },
  { key: 'ShapeFactor4',    group: 'Hệ số SF',   unit: 'tỷ lệ', desc: 'Hệ số hình dạng 4: Area / ((Major/2)(Minor/2)π).' }
];

const PCA_VARIANCE_RATIO = [
  0.5547, 0.2644, 0.0801, 0.0468, 0.0274, 0.0115, 0.0069, 0.0033,
  0.0021, 0.0012, 0.0007, 0.0004, 0.0002, 0.00015, 0.0001, 0.00005
];

/**
 * 6 Bước thí nghiệm hướng dẫn trên thanh Timeline dưới đáy
 */
const GUIDED_EXPERIMENTS = [
  {
    step: 1,
    shortLabel: 'Dữ liệu chuẩn',
    badge: 'CƠ BẢN',
    badgeClass: 'bg-mint',
    title: 'Trạng thái chuẩn: 7 cụm trên mặt phẳng PC1–PC2',
    desc: 'Toàn bộ 13.611 hạt đậu được chiếu lên 2 thành phần chính đầu tiên (81.9% phương sai). Quan sát dấu chữ thập (+) của K-Means nằm lơ lửng giữa đám mây điểm, trong khi hạt sáng (◉) của K-Medoids là một hạt đậu có thật.',
    keyIdea: 'Tâm K-Means là trung bình cộng toán học nên có thể rơi vào vùng không tồn tại hạt nào; Medoid luôn là một hạt đậu thật đại diện cho cụm.',
    apply: () => {
      state.k = 7;
      state.pcaDims = 2;
      state.standardized = true;
      state.outliersInjected = false;
      state.selectedVariety = null;
    }
  },
  {
    step: 2,
    shortLabel: 'Đổi số cụm k',
    badge: 'THAM SỐ k',
    badgeClass: 'bg-yellow',
    title: 'Thử nghiệm k = 4: Gom theo nhóm kích thước – hình dáng lớn',
    desc: 'Khi giảm số cụm k từ 7 xuống 4, hai bản đồ đồng loạt chia lại không gian: Bombay tách riêng ở cực phải, Horoz tách ở cực trên, các giống hạt nhỏ gom chung.',
    keyIdea: 'Chỉ số ARI đạt đỉnh tại k = 7 (khớp với 7 giống đậu thực tế), trong khi Hệ số bóng (Silhouette) ưu tiên các cụm thưa lớn ở k nhỏ.',
    apply: () => {
      state.k = 4;
      state.pcaDims = 2;
      state.standardized = true;
      state.outliersInjected = false;
    }
  },
  {
    step: 3,
    shortLabel: 'Giảm chiều PCA',
    badge: 'CHIỀU PCA',
    badgeClass: 'bg-blue',
    title: 'Tăng chiều phân cụm lên d = 6 (98.5% phương sai)',
    desc: 'Phân cụm trên không gian 6 thành phần chính thay vì 2D giúp thuật toán tận dụng thêm thông tin độ đặc (Solidity) và độ lồi để tách ranh giới Cali – Barbunya.',
    keyIdea: 'Mặt phẳng PC1–PC2 dùng để quan sát trực quan, còn việc gom cụm ở d = 4..6 chiều giúp ARI tăng rõ rệt so với chỉ dùng 2 chiều.',
    apply: () => {
      state.k = 7;
      state.pcaDims = 6;
      state.standardized = true;
      state.outliersInjected = false;
    }
  },
  {
    step: 4,
    shortLabel: 'Tắt chuẩn hóa',
    badge: 'CẢNH BÁO SCALE',
    badgeClass: 'bg-yellow',
    title: 'Tắt StandardScaler: Cụm sụp về phân lớp theo diện tích',
    desc: 'Khi tắt chuẩn hóa, cột Area (hàng trăm nghìn px²) áp đảo >99.9% khoảng cách Euclide. Toàn bộ thông tin hình dáng trên trục dọc bị ép bẹp, biến phân cụm thành các lát cắt dọc.',
    keyIdea: 'Khoảng cách Euclide không bất biến với đơn vị đo. Không chuẩn hóa khiến các đặc trưng tỷ lệ (0–1) trở nên vô hình trước biến diện tích.',
    apply: () => {
      state.k = 7;
      state.pcaDims = 2;
      state.standardized = false;
      state.outliersInjected = false;
    }
  },
  {
    step: 5,
    shortLabel: 'Tiêm ngoại lai 1%',
    badge: 'ĐIỂM NHẤN',
    badgeClass: 'bg-coral',
    title: 'Tiêm ngoại lai 1%: Tâm K-Means nhảy lệch, Medoid đứng yên!',
    desc: 'Chỉ 1% số hạt (136 hạt) bị nhân cột kích thước lên ×10.5 lần. Nhìn bên trái: dấu chữ thập (+) bị kéo bật sang phải và ARI K-Means tụt thảm hại. Nhìn bên phải: hạt sáng Medoid (◉) gần như bất động!',
    keyIdea: 'K-Means tối thiểu hóa tổng bình phương khoảng cách (nhạy cảm cực độ với ngoại lai); K-Medoids tối thiểu hóa tổng khoảng cách tuyến tính nên kháng nhiễu.',
    apply: () => {
      state.k = 7;
      state.pcaDims = 2;
      state.standardized = true;
      state.outliersInjected = true;
    }
  },
  {
    step: 6,
    shortLabel: 'Soi 16 số đo',
    badge: 'KIỂM ĐỊNH HẠT',
    badgeClass: 'bg-lavender',
    title: 'Bấm chọn Medoid để đọc đủ 16 thông số hạt mẫu chuẩn',
    desc: 'Người phân loại nông sản có thể lấy chính hạt Medoid được tô sáng trên bản đồ bên phải để làm mẫu chuẩn đối chiếu trên dây chuyền phân loại thực tế.',
    keyIdea: 'Tính diễn giải thực tiễn: Medoid cung cấp một mẫu vật thật với đầy đủ 16 số đo vật lý thay vì một vector trung bình không tồn tại.',
    apply: () => {
      state.k = 7;
      state.pcaDims = 2;
      state.standardized = true;
      state.outliersInjected = false;
      state.selectedMedoidCluster = 6;
    }
  }
];

/**
 * Dữ liệu Bảng chính vs Bảng phụ sau tiêm ngoại lai 1% (10 seeds) - Mục B8
 */
const BENCHMARK_DATA = {
  2: [
    { k: 2,  cMed: '0.281±0.001', cKm: '0.279±0.001', cSil: '0.492±0.001', cTime: '0.38±0.02', oMed: '0.278±0.002', oKm: '0.014±0.003', oSil: '0.489±0.002', oTime: '0.41±0.03', dMed: -0.003, dKm: -0.265 },
    { k: 3,  cMed: '0.412±0.003', cKm: '0.409±0.002', cSil: '0.468±0.002', cTime: '0.46±0.03', oMed: '0.407±0.004', oKm: '0.182±0.008', oSil: '0.463±0.003', oTime: '0.49±0.03', dMed: -0.005, dKm: -0.227 },
    { k: 4,  cMed: '0.518±0.004', cKm: '0.521±0.003', cSil: '0.454±0.002', cTime: '0.55±0.03', oMed: '0.511±0.005', oKm: '0.279±0.011', oSil: '0.449±0.004', oTime: '0.58±0.04', dMed: -0.007, dKm: -0.242 },
    { k: 5,  cMed: '0.589±0.005', cKm: '0.594±0.004', cSil: '0.445±0.003', cTime: '0.67±0.04', oMed: '0.581±0.006', oKm: '0.331±0.014', oSil: '0.439±0.004', oTime: '0.71±0.04', dMed: -0.008, dKm: -0.263 },
    { k: 6,  cMed: '0.642±0.006', cKm: '0.648±0.005', cSil: '0.436±0.003', cTime: '0.79±0.04', oMed: '0.634±0.007', oKm: '0.365±0.015', oSil: '0.430±0.005', oTime: '0.84±0.05', dMed: -0.008, dKm: -0.283 },
    { k: 7,  cMed: '0.669±0.005', cKm: '0.674±0.004', cSil: '0.431±0.002', cTime: '0.92±0.05', oMed: '0.660±0.006', oKm: '0.385±0.016', oSil: '0.425±0.004', oTime: '0.97±0.06', dMed: -0.009, dKm: -0.289 },
    { k: 8,  cMed: '0.631±0.007', cKm: '0.637±0.006', cSil: '0.408±0.004', cTime: '1.08±0.06', oMed: '0.621±0.008', oKm: '0.371±0.018', oSil: '0.401±0.005', oTime: '1.14±0.07', dMed: -0.010, dKm: -0.266 },
    { k: 9,  cMed: '0.594±0.008', cKm: '0.601±0.007', cSil: '0.389±0.004', cTime: '1.24±0.07', oMed: '0.583±0.009', oKm: '0.354±0.019', oSil: '0.382±0.006', oTime: '1.31±0.08', dMed: -0.011, dKm: -0.247 },
    { k: 10, cMed: '0.562±0.009', cKm: '0.569±0.008', cSil: '0.374±0.005', cTime: '1.42±0.08', oMed: '0.550±0.010', oKm: '0.339±0.021', oSil: '0.366±0.006', oTime: '1.49±0.09', dMed: -0.012, dKm: -0.230 }
  ],
  4: [
    { k: 2,  cMed: '0.284±0.001', cKm: '0.282±0.001', cSil: '0.461±0.001', cTime: '0.44±0.02', oMed: '0.281±0.002', oKm: '0.015±0.003', oSil: '0.458±0.002', oTime: '0.47±0.03', dMed: -0.003, dKm: -0.267 },
    { k: 3,  cMed: '0.425±0.003', cKm: '0.421±0.002', cSil: '0.439±0.002', cTime: '0.53±0.03', oMed: '0.420±0.004', oKm: '0.191±0.007', oSil: '0.434±0.003', oTime: '0.57±0.03', dMed: -0.005, dKm: -0.230 },
    { k: 4,  cMed: '0.539±0.004', cKm: '0.542±0.003', cSil: '0.422±0.002', cTime: '0.64±0.03', oMed: '0.533±0.005', oKm: '0.294±0.010', oSil: '0.417±0.003', oTime: '0.68±0.04', dMed: -0.006, dKm: -0.248 },
    { k: 5,  cMed: '0.614±0.005', cKm: '0.619±0.004', cSil: '0.412±0.003', cTime: '0.78±0.04', oMed: '0.607±0.006', oKm: '0.352±0.013', oSil: '0.407±0.004', oTime: '0.82±0.04', dMed: -0.007, dKm: -0.267 },
    { k: 6,  cMed: '0.668±0.005', cKm: '0.673±0.004', cSil: '0.404±0.003', cTime: '0.91±0.05', oMed: '0.660±0.006', oKm: '0.391±0.015', oSil: '0.399±0.004', oTime: '0.96±0.05', dMed: -0.008, dKm: -0.282 },
    { k: 7,  cMed: '0.695±0.004', cKm: '0.701±0.004', cSil: '0.398±0.002', cTime: '1.06±0.05', oMed: '0.687±0.005', oKm: '0.412±0.015', oSil: '0.393±0.004', oTime: '1.12±0.06', dMed: -0.008, dKm: -0.289 },
    { k: 8,  cMed: '0.654±0.006', cKm: '0.660±0.005', cSil: '0.376±0.003', cTime: '1.22±0.06', oMed: '0.645±0.007', oKm: '0.394±0.017', oSil: '0.370±0.005', oTime: '1.29±0.07', dMed: -0.009, dKm: -0.266 },
    { k: 9,  cMed: '0.618±0.007', cKm: '0.624±0.006', cSil: '0.358±0.004', cTime: '1.39±0.07', oMed: '0.608±0.008', oKm: '0.376±0.018', oSil: '0.352±0.005', oTime: '1.46±0.08', dMed: -0.010, dKm: -0.248 },
    { k: 10, cMed: '0.584±0.008', cKm: '0.591±0.007', cSil: '0.342±0.004', cTime: '1.58±0.08', oMed: '0.573±0.009', oKm: '0.359±0.020', oSil: '0.336±0.006', oTime: '1.66±0.09', dMed: -0.011, dKm: -0.232 }
  ],
  16: [
    { k: 2,  cMed: '0.285±0.001', cKm: '0.283±0.001', cSil: '0.442±0.001', cTime: '0.62±0.03', oMed: '0.282±0.002', oKm: '0.016±0.003', oSil: '0.439±0.002', oTime: '0.66±0.04', dMed: -0.003, dKm: -0.267 },
    { k: 3,  cMed: '0.428±0.003', cKm: '0.424±0.002', cSil: '0.418±0.002', cTime: '0.75±0.04', oMed: '0.423±0.004', oKm: '0.194±0.008', oSil: '0.414±0.003', oTime: '0.79±0.04', dMed: -0.005, dKm: -0.230 },
    { k: 4,  cMed: '0.543±0.004', cKm: '0.546±0.003', cSil: '0.401±0.002', cTime: '0.91±0.04', oMed: '0.537±0.005', oKm: '0.298±0.011', oSil: '0.396±0.003', oTime: '0.96±0.05', dMed: -0.006, dKm: -0.248 },
    { k: 5,  cMed: '0.619±0.005', cKm: '0.623±0.004', cSil: '0.391±0.003', cTime: '1.09±0.05', oMed: '0.612±0.006', oKm: '0.356±0.014', oSil: '0.386±0.004', oTime: '1.15±0.06', dMed: -0.007, dKm: -0.267 },
    { k: 6,  cMed: '0.672±0.005', cKm: '0.677±0.004', cSil: '0.383±0.003', cTime: '1.28±0.06', oMed: '0.664±0.006', oKm: '0.395±0.015', oSil: '0.378±0.004', oTime: '1.35±0.07', dMed: -0.008, dKm: -0.282 },
    { k: 7,  cMed: '0.701±0.004', cKm: '0.706±0.004', cSil: '0.378±0.002', cTime: '1.48±0.07', oMed: '0.692±0.005', oKm: '0.415±0.016', oSil: '0.373±0.004', oTime: '1.56±0.08', dMed: -0.009, dKm: -0.291 },
    { k: 8,  cMed: '0.659±0.006', cKm: '0.665±0.005', cSil: '0.356±0.003', cTime: '1.71±0.08', oMed: '0.650±0.007', oKm: '0.397±0.018', oSil: '0.350±0.005', oTime: '1.80±0.09', dMed: -0.009, dKm: -0.268 },
    { k: 9,  cMed: '0.622±0.007', cKm: '0.629±0.006', cSil: '0.339±0.004', cTime: '1.94±0.09', oMed: '0.612±0.008', oKm: '0.379±0.019', oSil: '0.333±0.005', oTime: '2.04±0.10', dMed: -0.010, dKm: -0.250 },
    { k: 10, cMed: '0.589±0.008', cKm: '0.595±0.007', cSil: '0.324±0.004', cTime: '2.19±0.10', oMed: '0.578±0.009', oKm: '0.362±0.021', oSil: '0.318±0.006', oTime: '2.31±0.11', dMed: -0.011, dKm: -0.233 }
  ]
};

/**
 * Bộ sinh số ngẫu nhiên xác định Mulberry32 để đảm bảo tái lập 100%
 */
function createRng(seed) {
  let a = seed >>> 0;
  return function () {
    let t = a += 0x6D2B79F5;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function gaussianRng(rng) {
  let u = 0, v = 0;
  while (u === 0) u = rng();
  while (v === 0) v = rng();
  return Math.sqrt(-2.0 * Math.log(u)) * Math.cos(2.0 * Math.PI * v);
}

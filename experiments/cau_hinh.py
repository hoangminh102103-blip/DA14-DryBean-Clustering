"""Cấu hình trung tâm cho toàn bộ thực nghiệm DA-14 (hạt giống & siêu tham số)."""

# Hạt giống ngẫu nhiên gốc — cố định tại một nơi duy nhất theo quy ước đồ án
HAT_GIONG = 20262027
SO_LAN_CHAY = 10
TY_LE_KIEM_TRA = 0.2

SEEDS_DAY_DU = [HAT_GIONG + i for i in range(SO_LAN_CHAY)]
SEEDS_NHANH = [HAT_GIONG, HAT_GIONG + 1]

# Lấy mẫu phân tầng cho PAM do ma trận 13.611 x 13.611 chiếm ~1,48 GB
N_MAU_DAY_DU = 3000
N_MAU_NHANH = 600

# Tham số thuật toán & thí nghiệm tiêm ngoại lai
N_INIT_KMEANS = 10
TY_LE_NGOAI_LAI = 0.01
HE_SO_NGOAI_LAI = (8.0, 12.0)
COT_NGOAI_LAI = "Area"

# Lưới khảo sát chiều PCA (TN-A) và số cụm k (TN-B)
LUOI_D_TNA = list(range(2, 17))
LUOI_D_TNB = [2, 4, 16]
LUOI_KC_TNB = list(range(2, 17))

# Tham số hướng mở rộng A (Mahalanobis qua SVD)
NGUONG_CAT_SVD_MAHAL = 1e-3
TIKHONOV_LAMBDA = 1e-4

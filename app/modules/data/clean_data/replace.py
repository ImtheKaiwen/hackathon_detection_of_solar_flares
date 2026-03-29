import pandas as pd
import numpy as np
from pathlib import Path
import pickle

# =========================
# 1) DOSYA YOLLARI
# =========================
CURRENT_DIR = Path(__file__).resolve().parent
input_csv = CURRENT_DIR / "SWANSF_FPCKNN_LSBZM_Final.csv"
output_hourly_csv = CURRENT_DIR / "tahmine_hazir_veri.csv"
output_npy = CURRENT_DIR / "X_3d_harpnum_samples.npy"
output_pkl = CURRENT_DIR / "X_3d_harpnum_samples.pkl"

# =========================
# 2) 24 FEATURE SÜTUNU
# =========================
feature_cols = [
    "r_value", "totusjh", "totbsq", "totpot", "totusjz", "absnjzh",
    "savncpp", "usflux", "totfz", "meanpot", "epsx", "epsy", "epsz",
    "meanshr", "shrgt45", "meangam", "meangbt", "meangbz", "meangbh",
    "meanjzh", "totfy", "meanjzd", "meanalp", "totfx"
]

meta_cols_to_drop = ["harpnum", "t_rec", "noaa_ars", "t_rec_dt", "fetched_at_utc"]

# =========================
# 3) CSV'Yİ OKU
# =========================
df = pd.read_csv(input_csv)

# t_rec_dt'yi datetime yap
df["t_rec_dt"] = pd.to_datetime(df["t_rec_dt"])

# Güvenlik kontrolü
required_cols = ["harpnum", "t_rec", "noaa_ars", "t_rec_dt", "fetched_at_utc"] + feature_cols
missing_cols = [c for c in required_cols if c not in df.columns]
if missing_cols:
    raise ValueError(f"Eksik sütun(lar) var: {missing_cols}")

# =========================
# 4) HER HARPNUM İÇİN
#    SON KAYITTAN GERİYE DOĞRU
#    1 SAATLİK 60 ZAMAN NOKTASI OLUŞTUR
# =========================
all_hourly_rows = []

for harpnum, group in df.groupby("harpnum"):
    group = group.sort_values("t_rec_dt").reset_index(drop=True)

    # Bu harpnum'un en son zamanı
    last_time = group["t_rec_dt"].max()

    # En sondan geriye doğru 60 adet 1 saatlik zaman noktası
    # örn: last_time - 59 saat ... last_time
    target_times = pd.date_range(end=last_time, periods=60, freq="1h")

    target_df = pd.DataFrame({
        "harpnum": harpnum,
        "target_time": target_times
    })

    # merge_asof için iki tarafın da sıralı olması gerekir
    group_for_merge = group.sort_values("t_rec_dt").copy()
    target_df = target_df.sort_values("target_time").copy()

    # Her hedef zamana en yakın gerçek kaydı bağla
    # tolerance istersen ayarlayabilirsin. Şu an 40 dk verdim.
    merged = pd.merge_asof(
        left=target_df,
        right=group_for_merge,
        left_on="target_time",
        right_on="t_rec_dt",
        direction="nearest",
        tolerance=pd.Timedelta("40min")
    )

    # merge_asof sonrasında harpnum sütunu harpnum_x/harpnum_y olarak gelebilir.
    if "harpnum" not in merged.columns:
        if "harpnum_x" in merged.columns:
            merged["harpnum"] = merged["harpnum_x"]
        elif "harpnum_y" in merged.columns:
            merged["harpnum"] = merged["harpnum_y"]
        else:
            merged["harpnum"] = harpnum

    # Eğer bazı saatlerde eşleşme bulunamazsa:
    # önce ileri/geri doldurma ile tamamla
    merged = merged.sort_values("target_time").reset_index(drop=True)
    merged[feature_cols] = merged[feature_cols].ffill().bfill()

    # İstersen target_time'ı da t_rec_dt yerine ana zaman ekseni gibi saklayabilirsin
    merged["t_rec_dt"] = merged["target_time"]

    # t_rec alanını bu yeni saatlik zamana göre yeniden üretelim
    merged["t_rec"] = merged["t_rec_dt"].dt.strftime("%Y.%m.%d_%H:%M:%S_TAI")

    all_hourly_rows.append(merged)

# Tüm harpnum'ları birleştir
hourly_df = pd.concat(all_hourly_rows, ignore_index=True)

# noaa_ars ve fetched_at_utc eksik gelmiş olabilir; varsa koru, yoksa boş bırak
for c in ["noaa_ars", "fetched_at_utc"]:
    if c not in hourly_df.columns:
        hourly_df[c] = np.nan

# İstersen sıralama:
hourly_df = hourly_df.sort_values(["harpnum", "t_rec_dt"]).reset_index(drop=True)

# =========================
# 5) ARA ÇIKTIYI CSV OLARAK KAYDET
#    (60 saatlik, harpnum bazlı zaman serisi)
# =========================
hourly_df.to_csv(output_hourly_csv, index=False, encoding="utf-8-sig")
print(f"tahmine_hazir_veri.csv olarak kaydedildi: {output_hourly_csv}")

# =========================
# 6) 3 BOYUTLU HALE GETİR
#    (num_samples, 60, 24)
#    her harpnum = 1 sample
# =========================
# Önce istenmeyen meta sütunları kaldıracağız ama gruplayabilmek için
# harpnum'u geçici olarak kullanacağız.
samples = []
sample_harpnums = []

for harpnum, group in hourly_df.groupby("harpnum"):
    group = group.sort_values("t_rec_dt").reset_index(drop=True)

    # Güvenlik: tam 60 satır var mı?
    if len(group) != 60:
        print(f"UYARI: harpnum={harpnum} için satır sayısı 60 değil, atlandı. Satır sayısı = {len(group)}")
        continue

    # Meta sütunlarını kaldır -> geriye sadece 24 feature kalsın
    X_part = group.drop(columns=meta_cols_to_drop, errors="ignore")

    # Sütun sırasını garanti altına al
    X_part = X_part[feature_cols]

    # numpy array'e çevir
    X_part = X_part.to_numpy(dtype=np.float32)

    # shape kontrol
    if X_part.shape != (60, 24):
        print(f"UYARI: harpnum={harpnum} shape beklenenden farklı: {X_part.shape}")
        continue

    samples.append(X_part)
    sample_harpnums.append(harpnum)

# 3D numpy array
if not samples:
    raise ValueError("Hiç uygun örnek üretilemedi. Girdi verisini ve zaman eşleştirme toleransını kontrol et.")

X_3d = np.stack(samples, axis=0)  # (num_samples, 60, 24)

# Kaydet
np.save(output_npy, X_3d)

# Pickle formatında da kaydet
with open(output_pkl, "wb") as f:
    pickle.dump(X_3d, f)

print("3D veri oluşturuldu.")
print("X_3d shape:", X_3d.shape)
print("Kaydedilen dosya (NPY):", output_npy)
print("Kaydedilen dosya (PKL):", output_pkl)
print("Sample harpnum listesi:", sample_harpnums)
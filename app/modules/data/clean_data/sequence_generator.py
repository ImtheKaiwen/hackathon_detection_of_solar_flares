import pandas as pd
import numpy as np
from pathlib import Path
import pickle

class TimeSequenceGenerator:
    """
    Ön işlemesi tamamlanmış zaman serisi verisini okuyarak, 
    her 'harpnum' için belirtilen zaman adımında (örn: 60 saat) 3 boyutlu 
    (num_samples, time_steps, features) numpy dizisine dönüştürür.
    """
    
    def __init__(self, time_steps=60, freq="1h", tolerance="40min"):
        # Dosya Yolları
        self.current_dir = Path(__file__).resolve().parent
        self.input_csv = self.current_dir / "data/SWANSF_FPCKNN_LSBZM_Final.csv"
        self.output_hourly_csv = self.current_dir / "data/tahmine_hazir_veri.csv"
        self.output_npy = self.current_dir / "X_3d_harpnum_samples.npy"
        self.output_pkl = self.current_dir / "X_3d_harpnum_samples.pkl"
        
        # Parametreler
        self.time_steps = time_steps
        self.freq = freq
        self.tolerance = tolerance
        
        # Sütun Tanımlamaları
        self.feature_cols = [
            "r_value", "totusjh", "totbsq", "totpot", "totusjz", "absnjzh",
            "savncpp", "usflux", "totfz", "meanpot", "epsx", "epsy", "epsz",
            "meanshr", "shrgt45", "meangam", "meangbt", "meangbz", "meangbh",
            "meanjzh", "totfy", "meanjzd", "meanalp", "totfx"
        ]
        self.meta_cols_to_drop = ["harpnum", "t_rec", "noaa_ars", "t_rec_dt", "fetched_at_utc"]

    def _load_and_validate_data(self):
        """Veriyi yükler ve gerekli sütunların varlığını kontrol eder."""
        print(f"--- Veri okunuyor: {self.input_csv} ---")
        df = pd.read_csv(self.input_csv)
        df["t_rec_dt"] = pd.to_datetime(df["t_rec_dt"])

        required_cols = ["harpnum", "t_rec", "noaa_ars", "t_rec_dt", "fetched_at_utc"] + self.feature_cols
        missing_cols = [c for c in required_cols if c not in df.columns]
        
        if missing_cols:
            raise ValueError(f"Eksik sütun(lar) var: {missing_cols}")
            
        return df

    def _align_to_hourly_steps(self, df):
        """Her harpnum için son kayıttan geriye doğru sabit zaman aralıklı veri oluşturur."""
        print(f"--- Her harpnum için {self.time_steps} adımlık ({self.freq}) seriler oluşturuluyor ---")
        all_hourly_rows = []

        for harpnum, group in df.groupby("harpnum"):
            group = group.sort_values("t_rec_dt").reset_index(drop=True)
            last_time = group["t_rec_dt"].max()

            # En sondan geriye doğru hedef zaman noktaları
            target_times = pd.date_range(end=last_time, periods=self.time_steps, freq=self.freq)

            target_df = pd.DataFrame({
                "harpnum": harpnum,
                "target_time": target_times
            }).sort_values("target_time")

            group_for_merge = group.sort_values("t_rec_dt").copy()

            # Zamana göre en yakın kaydı eşleştir
            merged = pd.merge_asof(
                left=target_df,
                right=group_for_merge,
                left_on="target_time",
                right_on="t_rec_dt",
                direction="nearest",
                tolerance=pd.Timedelta(self.tolerance)
            )

            # Sütun çakışmalarını düzelt
            if "harpnum" not in merged.columns:
                merged["harpnum"] = merged.get("harpnum_x", merged.get("harpnum_y", harpnum))

            # Eksikleri doldur ve zaman damgalarını güncelle
            merged = merged.sort_values("target_time").reset_index(drop=True)
            merged[self.feature_cols] = merged[self.feature_cols].ffill().bfill()
            
            merged["t_rec_dt"] = merged["target_time"]
            merged["t_rec"] = merged["t_rec_dt"].dt.strftime("%Y.%m.%d_%H:%M:%S_TAI")

            all_hourly_rows.append(merged)

        # Tüm grupları birleştir
        hourly_df = pd.concat(all_hourly_rows, ignore_index=True)

        for c in ["noaa_ars", "fetched_at_utc"]:
            if c not in hourly_df.columns:
                hourly_df[c] = np.nan

        return hourly_df.sort_values(["harpnum", "t_rec_dt"]).reset_index(drop=True)

    def _create_3d_array(self, hourly_df):
        """2 Boyutlu saatlik veriyi (num_samples, time_steps, features) formatında 3D array'e çevirir."""
        print("--- 3 Boyutlu (3D) tensör oluşturuluyor ---")
        samples = []
        sample_harpnums = []

        for harpnum, group in hourly_df.groupby("harpnum"):
            group = group.sort_values("t_rec_dt").reset_index(drop=True)

            if len(group) != self.time_steps:
                print(f"UYARI: harpnum={harpnum} için satır sayısı {self.time_steps} değil, atlandı. (Satır: {len(group)})")
                continue

            # Özellikleri ayır ve Numpy dizisine çevir
            X_part = group.drop(columns=self.meta_cols_to_drop, errors="ignore")[self.feature_cols]
            X_part_array = X_part.to_numpy(dtype=np.float32)

            if X_part_array.shape != (self.time_steps, len(self.feature_cols)):
                print(f"UYARI: harpnum={harpnum} shape beklenenden farklı: {X_part_array.shape}")
                continue

            samples.append(X_part_array)
            sample_harpnums.append(harpnum)

        if not samples:
            raise ValueError("Hiç uygun örnek üretilemedi. Girdi verisini ve zaman eşleştirme toleransını kontrol et.")

        return np.stack(samples, axis=0), sample_harpnums

    def generate(self):
        """Tüm süreci çalıştırır, 2D DataFrame'i ve 3D dizileri kaydedip döndürür."""
        try:
            # 1. Yükle ve Doğrula
            df = self._load_and_validate_data()
            
            # 2. Saatlik/Adımlık formata getir
            hourly_df = self._align_to_hourly_steps(df)
            
            # Ara çıktıyı kaydet
            hourly_df.to_csv(self.output_hourly_csv, index=False, encoding="utf-8-sig")
            print(f"Ara çıktı kaydedildi: {self.output_hourly_csv}")
            
            # 3. 3D tensöre dönüştür
            X_3d, sample_harpnums = self._create_3d_array(hourly_df)
            
            # NPY ve PKL olarak kaydet
            np.save(self.output_npy, X_3d)
            with open(self.output_pkl, "wb") as f:
                pickle.dump(X_3d, f)
                
            print("\nBAŞARILI!")
            print(f"X_3d shape: {X_3d.shape}")
            print(f"Kaydedilen dosya (NPY): {self.output_npy}")
            print(f"Kaydedilen dosya (PKL): {self.output_pkl}")
            
            return X_3d, hourly_df, sample_harpnums

        except Exception as e:
            print(f"\nHATA: {e}")
            return None, None, None

# Test bloğu
# if __name__ == "__main__":
#     # Varsayılan değerlerle (60 adım, 1 saat, 40dk tolerans) çalıştır
#     generator = TimeSequenceGenerator(time_steps=60, freq="1h", tolerance="40min")
#     X_3d, df_hourly, harpnum_list = generator.generate()
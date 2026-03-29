import pandas as pd
import numpy as np
import os
from sklearn.cluster import KMeans
from sklearn.impute import KNNImputer
from sklearn.preprocessing import MinMaxScaler
from scipy import stats
from tqdm import tqdm

class DataProcessor:
    """
    SWANSF veri seti için FPCKNN ve LSBZM algoritmalarını uygulayan veri işleme sınıfı.
    """
    
    def __init__(self, dont_touch_cols=None, n_clusters=3, n_neighbors=5):
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_root_dir = os.path.dirname(self.current_dir)
        
        # Sınıf başlatıldığında kullanılacak varsayılan dosya yolları
        self.input_candidates = [
            os.path.join(self.current_dir, "data/veriler_72saat_filled.csv"),
            os.path.join(self.current_dir, "data/veriler_72saat_filled_bunu_kullancaz.csv"),
            os.path.join(self.data_root_dir, "clean_data", "data/veriler_72saat_filled.csv"),
            os.path.join(self.data_root_dir, "fetch_data", "data/veriler_72saat_filled.csv"),
        ]
        self.output_path = os.path.join(self.current_dir, "data/SWANSF_FPCKNN_LSBZM_Final.csv")
        
        # Parametreler
        self.dont_touch = dont_touch_cols if dont_touch_cols is not None else ["harpnum", "t_rec"]
        self.n_clusters = n_clusters
        self.n_neighbors = n_neighbors

    def _load_data(self):
        """Uygun CSV dosyasını arar ve DataFrame olarak döndürür."""
        csv_path = next((p for p in self.input_candidates if os.path.exists(p)), None)
        
        if csv_path is None:
            raise FileNotFoundError(
                "Girdi dosyası bulunamadı. Beklenen dosyalardan biri yok:\n" + 
                "\n".join(self.input_candidates)
            )
            
        print(f"--- Veri yükleniyor ---")
        print(f"Kullanılan girdi dosyası: {csv_path}")
        return pd.read_csv(csv_path)

    def apply_fpcknn(self, features_df):
        """KMeans ile kümeleme yapar ve kümeler içinde KNN Imputer uygular."""
        print("\n--- FPCKNN uygulanıyor ---")
        
        # KMeans çalışabilsin diye geçici ortalama doldurma
        temp_fill = features_df.fillna(features_df.mean())

        # Kümeleme
        kmeans = KMeans(n_clusters=self.n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(temp_fill)

        features_df_with_cluster = features_df.copy()
        features_df_with_cluster["cluster"] = cluster_labels

        imputed_parts = []

        for cluster_id in range(self.n_clusters):
            cluster_data = features_df_with_cluster[features_df_with_cluster["cluster"] == cluster_id].copy()
            cluster_features = cluster_data.drop(columns=["cluster"])

            if cluster_features.isnull().sum().sum() > 0:
                imputer = KNNImputer(n_neighbors=self.n_neighbors)
                imputed_array = imputer.fit_transform(cluster_features)
                imputed_df = pd.DataFrame(
                    imputed_array,
                    columns=cluster_features.columns,
                    index=cluster_features.index
                )
            else:
                imputed_df = cluster_features.copy()

            imputed_parts.append(imputed_df)

        df_imputed = pd.concat(imputed_parts).sort_index()
        print("FPCKNN tamamlandı.")
        return df_imputed

    def apply_lsbzm(self, df_imputed, cols_to_process):
        """Verilen sütunlar üzerinde çarpıklık (skewness) bazlı dönüşüm ve ölçekleme yapar."""
        print("\n--- LSBZM uygulanıyor ---")
        
        for col_name in tqdm(cols_to_process, desc="LSBZM İşleniyor"):
            col = df_imputed[col_name].copy()

            # Tamamı NaN ise geç
            if col.isnull().all():
                print(f"Uyarı: {col_name} sütunu tamamen boş, atlandı.")
                continue

            # Sabit sütun ise direkt 0 yap
            if col.nunique(dropna=True) <= 1:
                df_imputed[col_name] = 0.0
                continue

            the_min = col.min()
            the_max = col.max()
            skewness = stats.skew(col.dropna())
            transformed = None

            # LSBZM mantığı
            if (the_max - the_min > 100000) or (the_max < 1 and the_min > -1):
                shift = 2 * abs(the_min) if the_min < 0 else 0.1
                all_pos = col + shift

                if skewness > 1:
                    transformed = np.log(all_pos + 1e-9)
                elif skewness < -1:
                    transformed = np.sqrt(all_pos)
                else:
                    transformed = stats.zscore(col, nan_policy="omit")
            else:
                if abs(skewness) > 1:
                    shift = 2 * abs(the_min) if the_min < 0 else 0.1
                    safe_col = col + shift

                    try:
                        transformed, _ = stats.boxcox(safe_col)
                    except Exception:
                        transformed = stats.zscore(col, nan_policy="omit")
                else:
                    transformed = stats.zscore(col, nan_policy="omit")

            # Eğer dönüşüm sonunda NaN oluşursa güvenli doldurma
            transformed = np.array(transformed, dtype=float)
            transformed = np.nan_to_num(transformed, nan=0.0, posinf=0.0, neginf=0.0)

            # Min-Max ölçekleme
            scaler = MinMaxScaler()
            scaled = scaler.fit_transform(transformed.reshape(-1, 1)).flatten()
            
            df_imputed[col_name] = scaled

        print("LSBZM tamamlandı.")
        return df_imputed

    def process_and_save(self):
        """Tüm boru hattını (pipeline) çalıştırır ve sonucu kaydeder."""
        try:
            df = self._load_data()
            
            # Sadece sayısal sütunları seç ve dokunulmayacakları çıkar
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            cols_to_process = [col for col in numeric_cols if col not in self.dont_touch]

            if not cols_to_process:
                raise ValueError("İşlem yapılacak uygun sayısal sütun bulunamadı.")

            print(f"İşlenecek sütun sayısı: {len(cols_to_process)}")
            print(f"Dokunulmayacak sütunlar: {self.dont_touch}")

            features_df = df[cols_to_process].copy()

            # 1. Aşama: FPCKNN (Eksik Veri Doldurma)
            df_imputed = self.apply_fpcknn(features_df)

            # 2. Aşama: LSBZM (Dönüşüm ve Ölçekleme)
            df_imputed_scaled = self.apply_lsbzm(df_imputed, cols_to_process)

            # 3. Aşama: Sonuçları ana dataframe'e geri yaz ve kaydet
            df_result = df.copy()
            df_result[cols_to_process] = df_imputed_scaled[cols_to_process]
            
            df_result.to_csv(self.output_path, index=False)

            print("\nBAŞARILI!")
            print(f"Çıktı dosyası: {self.output_path}")
            print(f"{', '.join(self.dont_touch)} sütunlarına işlem uygulanmadı.")
            
            return df_result

        except Exception as e:
            print(f"\nHATA: {e}")
            return None

# # Dosya direkt çalıştırılırsa test et
# if __name__ == "__main__":
#     processor = DataProcessor()
#     processor.process_and_save()
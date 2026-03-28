import pandas as pd
import numpy as np
import os
import pickle
from sklearn.cluster import KMeans
from sklearn.impute import KNNImputer
from sklearn.preprocessing import MinMaxScaler
from scipy import stats
from tqdm import tqdm

# --- AYARLAR ---
current_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(current_dir, 'veriler_72saat_filled_bunu_kullancaz.csv')
output_name = os.path.join(current_dir, "SWANSF_FPCKNN_LSBZM_Final.csv")

try:
    print(f"--- FPCKNN + AKADEMİK LSBZM İşlemi Başladı ---")
    df = pd.read_csv(csv_path)
    numeric_df = df.select_dtypes(include=[np.number])

    # ==========================================
    # ADIM 1: FPCKNN (ATAMA)
    # ==========================================
    print("FPCKNN Ataması yapılıyor...")
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    # Kümeleri belirlemek için geçici doldurma
    temp_fill = numeric_df.fillna(numeric_df.mean())
    clusters = kmeans.fit_predict(temp_fill)
    numeric_df['cluster'] = clusters

    imputed_list = []
    for cid in range(3):
        cluster_data = numeric_df[numeric_df['cluster'] == cid]
        if cluster_data.isnull().sum().sum() > 0:
            imputer = KNNImputer(n_neighbors=5)
            imputed_list.append(imputer.fit_transform(cluster_data))
        else:
            imputed_list.append(cluster_data.values)
    
    # Küme sütununu atarak temiz veriyi oluştur
    df_imputed = pd.DataFrame(np.vstack(imputed_list), columns=numeric_df.columns).drop(columns=['cluster'])
    print("Atama Bitti.")

    # ==========================================
    # ADIM 2: LSBZM (ARKADAŞININ ÖZEL MOTORU)
    # ==========================================
    print("Akademik LSBZM Normalizasyonu Başladı...")
    target_column = 'label'
    if target_column in df_imputed.columns:
        features = df_imputed.drop(columns=[target_column])
        labels = df_imputed[target_column]
    else:
        features = df_imputed
        labels = None

    data_array = features.values
    num_rows, num_cols = data_array.shape
    normalized_array = np.zeros((num_rows, num_cols))
    scaler = MinMaxScaler()

    # Sütun sütun arkadaşının mantığını uyguluyoruz
    for j in tqdm(range(num_cols), desc="LSBZM İşleniyor"):
        col = data_array[:, j]
        the_min = np.min(col)
        the_max = np.max(col)
        skewness = stats.skew(col)
        std_val = np.std(col)

        # Sabit sütun kontrolü (eğer sütun hep aynı sayıysa)
        if std_val == 0:
            normalized_col = np.ones(num_rows)
        else:
            # Arkadaşının Skewness (Çarpıklık) Karar Mekanizması
            if (the_max - the_min > 100000) or (the_max < 1 and the_min > -1):
                # Pozitife çek (Log ve Sqrt eksi sevmez)
                shift = 2 * abs(the_min) if the_min < 0 else 0.1
                all_pos = col + shift
                
                if skewness > 1: # Sağa çarpık (Log dönüşümü)
                    transformed = np.log(all_pos + 1e-9)
                elif skewness < -1: # Sola çarpık (Karekök dönüşümü)
                    transformed = np.sqrt(all_pos)
                else: # Normal (Z-Score)
                    transformed = stats.zscore(col)
            else:
                # Genel durum (Box-Cox veya Z-score)
                if skewness > 1 or skewness < -1:
                    # Box-Cox sadece pozitif veriyle çalışır
                    shift = 2 * abs(the_min) if the_min < 0 else 0.1
                    try:
                        transformed, _ = stats.boxcox(col + shift)
                    except:
                        transformed = stats.zscore(col)
                else:
                    transformed = stats.zscore(col)

            # TÜM YOLLAR SONUNDA 0-1 ARASINA ÇIKAR (Modelin istediği şey)
            data_2d = transformed.reshape(-1, 1)
            normalized_col = scaler.fit_transform(data_2d).flatten()

        normalized_array[:, j] = normalized_col

    # Veriyi geri birleştir
    df_final = pd.DataFrame(normalized_array, columns=features.columns)
    if labels is not None:
        df_final[target_column] = labels.values

    # Kaydet
    df_final.to_csv(output_name, index=False)
    print(f"\nİŞLEM TAMAM! Dosya: {output_name}")

except Exception as e:
    print(f"HATA: {e}")
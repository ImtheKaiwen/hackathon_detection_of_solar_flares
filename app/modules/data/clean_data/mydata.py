import pandas as pd
import numpy as np
import os
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

    # 1. ADIM: SİLİNMESİNİ İSTEMEDİĞİMİZ SÜTUNLARI KENARA AYIRALIM
    # Eğer bu sütunlar veride yoksa hata almamak için kontrol ekledik
    protected_cols = ['id', 't_ranch', 'label'] 
    existing_protected = [c for c in protected_cols if c in df.columns]
    
    # İşlem yapılacak sayısal veriyi ayır (ID ve T_RANCH'i buradan çıkarıyoruz)
    features_to_process = df.drop(columns=existing_protected).select_dtypes(include=[np.number])
    protected_df = df[existing_protected]

    # ==========================================
    # ADIM 2: FPCKNN (ATAMA)
    # ==========================================
    print("FPCKNN Ataması yapılıyor...")
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    # Kümeleri belirlemek için geçici doldurma
    temp_fill = features_to_process.fillna(features_to_process.mean())
    clusters = kmeans.fit_predict(temp_fill)
    features_to_process['cluster'] = clusters

    imputed_list = []
    for cid in range(3):
        cluster_data = features_to_process[features_to_process['cluster'] == cid]
        if cluster_data.isnull().sum().sum() > 0:
            imputer = KNNImputer(n_neighbors=5)
            imputed_list.append(imputer.fit_transform(cluster_data))
        else:
            imputed_list.append(cluster_data.values)
    
    df_imputed = pd.DataFrame(np.vstack(imputed_list), columns=features_to_process.columns).drop(columns=['cluster'])
    print("Atama Bitti.")

    # ==========================================
    # ADIM 3: LSBZM (AKADEMİK NORMALİZASYON)
    # ==========================================
    print("Akademik LSBZM Normalizasyonu Başladı...")
    data_array = df_imputed.values
    num_rows, num_cols = data_array.shape
    normalized_array = np.zeros((num_rows, num_cols))
    scaler = MinMaxScaler()

    for j in tqdm(range(num_cols), desc="LSBZM İşleniyor"):
        col = data_array[:, j]
        the_min, the_max = np.min(col), np.max(col)
        skewness = stats.skew(col)
        std_val = np.std(col)

        if std_val == 0:
            normalized_col = np.ones(num_rows)
        else:
            # Skewness Karar Mekanizması
            if (the_max - the_min > 100000) or (the_max < 1 and the_min > -1):
                shift = 2 * abs(the_min) if the_min < 0 else 0.1
                all_pos = col + shift
                transformed = np.log(all_pos + 1e-9) if skewness > 1 else (np.sqrt(all_pos) if skewness < -1 else stats.zscore(col))
            else:
                if skewness > 1 or skewness < -1:
                    shift = 2 * abs(the_min) if the_min < 0 else 0.1
                    try: transformed, _ = stats.boxcox(col + shift)
                    except: transformed = stats.zscore(col)
                else:
                    transformed = stats.zscore(col)

            normalized_col = scaler.fit_transform(transformed.reshape(-1, 1)).flatten()
        normalized_array[:, j] = normalized_col

    # ==========================================
    # ADIM 4: GERİ BİRLEŞTİRME (KORUNAN SÜTUNLARLA)
    # ==========================================
    df_final_features = pd.DataFrame(normalized_array, columns=df_imputed.columns)
    
    # Kenara ayırdığımız id, t_ranch ve label'ı geri ekliyoruz
    df_final = pd.concat([protected_df.reset_index(drop=True), df_final_features], axis=1)

    # Kaydet
    df_final.to_csv(output_name, index=False)
    print(f"\nİŞLEM TAMAM! {existing_protected} sütunları korundu.")
    print(f"Yeni Dosya: {output_name}")

except Exception as e:
    print(f"HATA: {e}")
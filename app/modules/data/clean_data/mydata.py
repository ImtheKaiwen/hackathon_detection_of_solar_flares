import pandas as pd
import numpy as np
import os
from sklearn.cluster import KMeans
from sklearn.impute import KNNImputer
from sklearn.preprocessing import MinMaxScaler
from scipy import stats
from tqdm import tqdm

current_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(current_dir, 'veriler_72saat_filled_bunu_kullancaz.csv')
output_name = os.path.join(current_dir, "SWANSF_FPCKNN_LSBZM_Final.csv")

try:
    print(f"--- Veri Yukleniyor ---")
    df = pd.read_csv(csv_path)

    # 1. ADIM: Sütun Ayıklama
    # Dokunulmayacaklar (Sayı olsa bile işleme girmeyecekler)
    dont_touch = ['id', 't_ranch', 'harpnum', 'label']
    
    # Gerçekten sayı olan ve işlem yapılması gereken sütunları bulalım
    # Sadece sayısal (int/float) tipindeki sütunları seçiyoruz
    all_numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # İşlem yapılacak sütunlar: Sayısal olanlar EKSİ dokunulmayacak olanlar
    cols_to_fix = [c for c in all_numeric_cols if c not in dont_touch]

    if not cols_to_fix:
        raise ValueError("İşlem yapılacak sayısal sütun bulunamadı! Sütun tiplerini kontrol et.")

    features_df = df[cols_to_fix].copy()

    # ==========================================
    # ADIM 2: FPCKNN (ATAMA)
    # ==========================================
    print("FPCKNN Atamasi yapiliyor...")
    # Sadece sayısal özellikler üzerinden ortalama alarak KMeans için ön dolgu yapıyoruz
    temp_fill = features_df.fillna(features_df.mean())
    
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(temp_fill)
    features_df['cluster'] = clusters

    imputed_list = []
    for cid in range(3):
        cluster_data = features_df[features_df['cluster'] == cid]
        data_only = cluster_data.drop(columns=['cluster'])
        
        if data_only.isnull().sum().sum() > 0:
            imputer = KNNImputer(n_neighbors=5)
            imputed_data = imputer.fit_transform(data_only)
            imputed_df = pd.DataFrame(imputed_data, columns=data_only.columns, index=data_only.index)
            imputed_list.append(imputed_df)
        else:
            imputed_list.append(data_only)
    
    df_imputed = pd.concat(imputed_list).sort_index()
    print("Atama Bitti.")

    # ==========================================
    # ADIM 3: LSBZM (NORMALIZASYON)
    # ==========================================
    print("LSBZM Normalizasyonu yapiliyor...")
    scaler = MinMaxScaler()
    
    for col_name in tqdm(cols_to_fix, desc="Islem Sirasi"):
        col = df_imputed[col_name]
        the_min, the_max = col.min(), col.max()
        # varyans kontrolü (tüm değerler aynıysa normalizasyon hata verir)
        if col.std() == 0:
            df_imputed[col_name] = 0.0
            continue
            
        skewness = stats.skew(col)
        
        # LSBZM + Skewness Logic
        if (the_max - the_min > 100000) or (the_max < 1 and the_min > -1):
            shift = 2 * abs(the_min) if the_min < 0 else 0.1
            all_pos = col + shift
            if skewness > 1: transformed = np.log(all_pos + 1e-9)
            elif skewness < -1: transformed = np.sqrt(all_pos)
            else: transformed = stats.zscore(col)
        else:
            if abs(skewness) > 1:
                shift = 2 * abs(the_min) if the_min < 0 else 0.1
                try: transformed, _ = stats.boxcox(col + shift)
                except: transformed = stats.zscore(col)
            else:
                transformed = stats.zscore(col)

        df_imputed[col_name] = scaler.fit_transform(np.array(transformed).reshape(-1, 1)).flatten()

    # ==========================================
    # ADIM 4: FINAL - BİRLEŞTİRME
    # ==========================================
    # Orijinal df'deki cols_to_fix sütunlarını yenileriyle güncelle
    df[cols_to_fix] = df_imputed[cols_to_fix]

    # Kaydet
    df.to_csv(output_name, index=False)
    print(f"\nBASARILI! {dont_touch} sutunlari korundu ve degismedi.")
    print(f"Cikti Dosyasi: {output_name}")

except Exception as e:
    print(f"\nHATA: {e}")
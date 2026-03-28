import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler  # Değişti: StandardScaler yerine MinMaxScaler
from sklearn.impute import SimpleImputer
import os

# DOSYA YOLUNU AYARLAMA
current_dir = os.path.dirname(os.path.abspath(__file__))
# Not: Dosya adındaki boşluklara dikkat et, hata alırsan tam adını kontrol et
csv_path = os.path.join(current_dir, 'veriler_72saat_filled_bunu_kullancaz.csv')
output_name = os.path.join(current_dir, "SWANSF_Optimize_Normalized_Data.csv")

try:
    print(f"--- Islem Basladi ---")
    print(f"Okunacak Dosya: {csv_path}")
    
    # 1. ADIM: Veriyi Yükleme
    df = pd.read_csv(csv_path) 
    print(f"Veri yüklendi. Satir sayisi: {len(df)}")

    # 2. ADIM: Sayisal sütunlari sec ve temizle
    numeric_df = df.select_dtypes(include=[np.number])
    print(f"Islenen sutun sayisi: {len(numeric_df.columns)}")

    imputer = SimpleImputer(strategy='mean')
    df_imputed_values = imputer.fit_transform(numeric_df)
    df_imputed = pd.DataFrame(df_imputed_values, columns=numeric_df.columns)
    print("Eksik veriler tamamlandi.")

    # 3. ADIM: Min-Max Normalizasyon (0-1 Arası)
    target_column = 'label' 
    if target_column in df_imputed.columns:
        features = df_imputed.drop(columns=[target_column])
        labels = df_imputed[target_column]
    else:
        features = df_imputed
        labels = None

    # Değişti: Artik veriler 0 ile 1 arasinda olacak, hic eksi kalmayacak
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_features = scaler.fit_transform(features)
    df_normalized = pd.DataFrame(scaled_features, columns=features.columns)

    if labels is not None:
        df_normalized[target_column] = labels.values
    print("Min-Max Normalizasyon (0-1) basariyla uygulandi.")

    # 4. ADIM: CSV Olarak Kaydetme
    df_normalized.to_csv(output_name, index=False)
    
    print("\n" + "="*40)
    print(f"ISLEM TAMAM! 0-1 Arasi verilerin hazir:")
    print(f"{output_name}")
    print("="*40)

except Exception as e:
    print(f"\nHATA OLUSTU: {e}")
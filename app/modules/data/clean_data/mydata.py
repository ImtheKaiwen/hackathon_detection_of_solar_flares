import pandas as pd
import numpy as np
import os
from sklearn.cluster import KMeans
from sklearn.impute import KNNImputer
from sklearn.preprocessing import MinMaxScaler
from scipy import stats
from tqdm import tqdm

# Dosya yolları
current_dir = os.path.dirname(os.path.abspath(__file__))
data_root_dir = os.path.dirname(current_dir)
input_candidates = [
    os.path.join(current_dir, "veriler_72saat_filled.csv"),
    os.path.join(current_dir, "veriler_72saat_filled_bunu_kullancaz.csv"),
    os.path.join(data_root_dir, "clean_data", "veriler_72saat_filled.csv"),
    os.path.join(data_root_dir, "fetch_data", "veriler_72saat_filled.csv"),
]
csv_path = next((p for p in input_candidates if os.path.exists(p)), None)
output_path = os.path.join(current_dir, "SWANSF_FPCKNN_LSBZM_Final.csv")

try:
    print("--- Veri yükleniyor ---")
    if csv_path is None:
        raise FileNotFoundError(
            "Girdi dosyası bulunamadı. Beklenen dosyalardan biri yok: "
            + ", ".join(input_candidates)
        )

    print(f"Kullanılan girdi dosyası: {csv_path}")
    df = pd.read_csv(csv_path)

    # Dokunulmayacak sütunlar
    dont_touch = ["harpnum", "t_rec"]

    # Sadece sayısal sütunları seç
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    # İşlem uygulanacak sütunlar = sayısal sütunlar - dokunulmayacaklar
    cols_to_process = [col for col in numeric_cols if col not in dont_touch]

    if not cols_to_process:
        raise ValueError("İşlem yapılacak uygun sayısal sütun bulunamadı.")

    print(f"İşlenecek sütunlar: {cols_to_process}")
    print(f"Dokunulmayacak sütunlar: {dont_touch}")

    # Sadece işlenecek sütunları al
    features_df = df[cols_to_process].copy()

    # =========================================================
    # 1) FPCKNN
    # =========================================================
    print("\n--- FPCKNN uygulanıyor ---")

    # KMeans çalışabilsin diye geçici ortalama doldurma
    temp_fill = features_df.fillna(features_df.mean())

    # Kümeleme
    n_clusters = 3
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(temp_fill)

    features_df_with_cluster = features_df.copy()
    features_df_with_cluster["cluster"] = cluster_labels

    imputed_parts = []

    for cluster_id in range(n_clusters):
        cluster_data = features_df_with_cluster[features_df_with_cluster["cluster"] == cluster_id].copy()
        cluster_features = cluster_data.drop(columns=["cluster"])

        if cluster_features.isnull().sum().sum() > 0:
            imputer = KNNImputer(n_neighbors=5)
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

    # =========================================================
    # 2) LSBZM
    # =========================================================
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

        # Skewness hesapla
        skewness = stats.skew(col.dropna())

        # Varsayılan dönüşüm
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

    # =========================================================
    # 3) Sonuçları ana dataframe'e geri yaz
    # =========================================================
    df_result = df.copy()
    df_result[cols_to_process] = df_imputed[cols_to_process]

    # harpnum ve t_rec aynen korunur
    # zaten cols_to_process içinde olmadıkları için değişmezler

    # Kaydet
    df_result.to_csv(output_path, index=False)

    print("\nBASARILI!")
    print(f"Çıktı dosyası: {output_path}")
    print("harpnum ve t_rec sütunlarına işlem uygulanmadı.")

except Exception as e:
    print(f"\nHATA: {e}")
from __future__ import annotations

from pathlib import Path
import pandas as pd


def run_fill_missing_features(
    input_csv: str = "veriler_72saat.csv",
    output_csv: str = "veriler_72saat_filled.csv",
) -> Path:
    """
    72 saatlik veriyi okuyup eksik feature değerlerini 0 ile doldurur
    ve yeni bir CSV dosyası olarak kaydeder.
    """

    input_path = Path(input_csv)
    output_path = Path(output_csv)

    if not input_path.exists():
        raise FileNotFoundError(f"Girdi dosyası bulunamadı: {input_path}")

    df = pd.read_csv(input_path)

    # Kimlik/zaman alanları dışındaki sütunları feature kabul ediyoruz
    non_feature_cols = {
        "harpnum",
        "t_rec",
        "t_rec_dt",
        "fetched_at_utc",
    }

    feature_cols = [col for col in df.columns if col not in non_feature_cols]

    missing_before = int(df[feature_cols].isna().sum().sum())

    df[feature_cols] = df[feature_cols].fillna(0)

    missing_after = int(df[feature_cols].isna().sum().sum())

    df.to_csv(output_path, index=False)

    print("\nEksik feature doldurma işlemi tamamlandı.")
    print(f"Girdi dosyası: {input_path}")
    print(f"Çıktı dosyası: {output_path}")
    print(f"Feature sütunu sayısı: {len(feature_cols)}")
    print(f"Doldurulan eksik değer sayısı: {missing_before}")
    print(f"Kalan eksik değer sayısı: {missing_after}")

    return output_path


def main() -> None:
    run_fill_missing_features()


if __name__ == "__main__":
    main()
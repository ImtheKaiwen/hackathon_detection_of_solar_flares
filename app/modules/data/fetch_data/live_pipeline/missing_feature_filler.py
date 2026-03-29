from __future__ import annotations
from pathlib import Path
import pandas as pd

class MissingFeatureFiller:
    def __init__(self):
        self.non_feature_cols = {"harpnum", "t_rec", "t_rec_dt", "fetched_at_utc"}

    def process(self, input_csv: Path, output_csv: Path) -> Path:
        if not input_csv.exists():
            raise FileNotFoundError(f"Girdi dosyası bulunamadı: {input_csv}")

        df = pd.read_csv(input_csv)
        feature_cols = [col for col in df.columns if col not in self.non_feature_cols]

        missing_before = int(df[feature_cols].isna().sum().sum())
        df[feature_cols] = df[feature_cols].fillna(0)
        
        output_csv.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_csv, index=False)

        print(f"✅ Eksik feature doldurma tamamlandı. ({missing_before} değer 0 ile dolduruldu)")
        return output_csv
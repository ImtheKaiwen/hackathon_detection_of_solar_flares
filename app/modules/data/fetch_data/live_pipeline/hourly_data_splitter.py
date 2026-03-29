from __future__ import annotations
from pathlib import Path
import pandas as pd

class HourlyDataSplitter:
    def _extract_last_n_hourly_rows(self, group_df: pd.DataFrame, hours: int) -> pd.DataFrame:
        group_df = group_df.copy().sort_values("t_rec_dt")
        group_df["hour_slot"] = group_df["t_rec_dt"].dt.floor("h")
        group_df = group_df.drop_duplicates(subset=["hour_slot"], keep="last")

        if group_df.empty:
            return pd.DataFrame()

        latest_time = group_df["hour_slot"].max()
        required_hours = pd.date_range(end=latest_time, periods=hours, freq="h")
        filtered = group_df[group_df["hour_slot"].isin(required_hours)].copy()

        if filtered["hour_slot"].nunique() != hours:
            return pd.DataFrame()

        return filtered.sort_values("hour_slot").reset_index(drop=True)

    def split(self, input_csv: Path, output_dir: Path, hours: int = 60) -> None:
        if not input_csv.exists():
            raise FileNotFoundError(f"Girdi dosyası bulunamadı: {input_csv}")

        output_dir.mkdir(parents=True, exist_ok=True)
        df = pd.read_csv(input_csv)
        
        df["t_rec_dt"] = pd.to_datetime(
            df["t_rec"].astype(str).str.replace("_TAI", "", regex=False),
            format="%Y.%m.%d_%H:%M:%S",
            errors="coerce"
        )
        
        df["harpnum"] = pd.to_numeric(df["harpnum"], errors="coerce")
        df = df.dropna(subset=["harpnum", "t_rec_dt"]).copy()
        df["harpnum"] = df["harpnum"].astype(int)

        harpnums = sorted(df["harpnum"].unique().tolist())
        exported_count = 0

        for harpnum in harpnums:
            group = df[df["harpnum"] == harpnum]
            result = self._extract_last_n_hourly_rows(group, hours=hours)

            if result.empty:
                print(f"HARPNUM {harpnum}: {hours} saatlik tam veri yok, atlandı.")
                continue

            output_path = output_dir / f"{harpnum}.csv"
            result.to_csv(output_path, index=False, encoding="utf-8")
            exported_count += 1

        print(f"✅ Bölme işlemi tamamlandı. {exported_count} HARPNUM klasöre aktarıldı: {output_dir}")
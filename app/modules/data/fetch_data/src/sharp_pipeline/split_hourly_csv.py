from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def parse_t_rec_column(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["t_rec_dt"] = pd.to_datetime(
        df["t_rec"].astype(str).str.replace("_TAI", "", regex=False),
        format="%Y.%m.%d_%H:%M:%S",
        errors="coerce",
    )
    return df


def extract_last_n_hourly_rows(group_df: pd.DataFrame, hours: int = 60) -> pd.DataFrame:
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


def export_groups_to_csv(df: pd.DataFrame, output_dir: str, hours: int = 60) -> tuple[int, int]:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    harpnums = sorted(df["harpnum"].dropna().astype(int).unique().tolist())
    exported_count = 0
    skipped_count = 0

    for harpnum in harpnums:
        group = df[df["harpnum"] == harpnum].copy()
        result = extract_last_n_hourly_rows(group, hours=hours)

        if result.empty:
            print(f"HARPNUM {harpnum}: tam {hours} saatlik saatlik veri yok, atlandı.")
            skipped_count += 1
            continue

        output_path = out_dir / f"{harpnum}.csv"
        result.to_csv(output_path, index=False, encoding="utf-8")
        print(f"HARPNUM {harpnum}: {len(result)} satır kaydedildi -> {output_path}")
        exported_count += 1

    print("\nİşlem tamamlandı.")
    print(f"Dışa aktarılan bölge sayısı: {exported_count}")
    print(f"Atlanan bölge sayısı: {skipped_count}")
    return exported_count, skipped_count


def run_split(input_csv: str = "veriler_72saat.csv", output_dir: str = "harpnum_csvler", hours: int = 60) -> None:
    df = pd.read_csv(input_csv)
    required_cols = ["harpnum", "t_rec"]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Gerekli kolon bulunamadı: {col}")

    df["harpnum"] = pd.to_numeric(df["harpnum"], errors="coerce")
    df = parse_t_rec_column(df)
    df = df.dropna(subset=["harpnum", "t_rec_dt"]).copy()
    df["harpnum"] = df["harpnum"].astype(int)
    export_groups_to_csv(df, output_dir, hours=hours)


def main() -> None:
    parser = argparse.ArgumentParser(description="Master CSV dosyasını HARPNUM bazlı ayırır.")
    parser.add_argument("--input-csv", default="veriler_72saat.csv")
    parser.add_argument("--output-dir", default="harpnum_csvler")
    parser.add_argument("--hours", type=int, default=60)
    args = parser.parse_args()
    run_split(input_csv=args.input_csv, output_dir=args.output_dir, hours=args.hours)


if __name__ == "__main__":
    main()

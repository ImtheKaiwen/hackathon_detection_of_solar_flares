from __future__ import annotations

import argparse

import pandas as pd

from .common import build_nrt_query, create_client, safe_query

KEYS = ["HARPNUM", "T_REC"]


def fetch_data(client, hours: int) -> pd.DataFrame:
    query = build_nrt_query(hours=hours)
    print(f"\nSorgu ({hours} saat): {query}")
    return safe_query(client, query, KEYS)


def get_latest_valid_timeslot(df: pd.DataFrame) -> tuple[pd.Timestamp | None, pd.DataFrame]:
    temp = df.copy()
    temp["T_REC_DT"] = pd.to_datetime(
        temp["T_REC"].astype(str).str.replace("_TAI", "", regex=False),
        format="%Y.%m.%d_%H:%M:%S",
        errors="coerce",
    )
    temp = temp.dropna(subset=["T_REC_DT", "HARPNUM"])
    if temp.empty:
        return None, pd.DataFrame()

    latest_time = temp["T_REC_DT"].max()
    latest_df = temp[temp["T_REC_DT"] == latest_time].copy()
    return latest_time, latest_df


def extract_harpnums(df: pd.DataFrame) -> list[int]:
    harpnums = (
        pd.to_numeric(df["HARPNUM"], errors="coerce")
        .dropna()
        .astype(int)
        .unique()
        .tolist()
    )
    harpnums.sort()
    return harpnums


def get_active_harpnums(primary_hours: int = 2, fallback_hours: int = 6) -> list[int]:
    client = create_client()

    df = fetch_data(client, hours=primary_hours)
    latest_time, latest_df = get_latest_valid_timeslot(df)

    if latest_df.empty:
        print(f"\n⚠️ {primary_hours} saat içinde veri yok → {fallback_hours} saate geçiliyor")
        df = fetch_data(client, hours=fallback_hours)
        latest_time, latest_df = get_latest_valid_timeslot(df)
        if latest_df.empty:
            print(f"❌ {fallback_hours} saat içinde de veri bulunamadı")
            return []

    harpnums = extract_harpnums(latest_df)
    print("\n📌 En son dolu zaman dilimi:")
    print(latest_time)
    print("\n📌 Aktif HARPNUM listesi:")
    print(harpnums)
    print(f"\nToplam bölge sayısı: {len(harpnums)}")
    return harpnums


def main() -> None:
    parser = argparse.ArgumentParser(description="Aktif HARPNUM listesini bulur.")
    parser.add_argument("--primary-hours", type=int, default=2)
    parser.add_argument("--fallback-hours", type=int, default=6)
    args = parser.parse_args()
    get_active_harpnums(primary_hours=args.primary_hours, fallback_hours=args.fallback_hours)


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import time
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

from .active_harpnums import get_active_harpnums
from .common import BASE_KEYS, QUERY_KEYS, create_client, parse_t_rec_to_datetime, safe_query, to_jsoc_tai_string


def fetch_recent_for_harpnum(client, harpnum: int, hours: int) -> pd.DataFrame:
    start_dt = datetime.utcnow() - timedelta(hours=hours)
    start_str = to_jsoc_tai_string(start_dt)
    query = f"hmi.sharp_720s_nrt[{harpnum}][{start_str}/{hours}h@12m]"
    print(f"Sorgu ({hours}s, HARPNUM={harpnum}): {query}")
    return safe_query(client, query, BASE_KEYS)


def get_latest_non_null_timeslot(
    client,
    harpnums: list[int],
    primary_hours: int = 2,
    fallback_hours: int = 6,
    sleep_between_requests: float = 1.0,
) -> datetime | None:
    for lookback in [primary_hours, fallback_hours]:
        collected = []
        print(f"\nEn son dolu zaman dilimi aranıyor: son {lookback} saat")

        for harpnum in harpnums:
            df = fetch_recent_for_harpnum(client, harpnum, lookback)
            if not df.empty:
                collected.append(df)
            time.sleep(sleep_between_requests)

        if not collected:
            print(f"Son {lookback} saatte hiç veri bulunamadı.")
            continue

        merged = pd.concat(collected, ignore_index=True)
        merged["T_REC_DT"] = parse_t_rec_to_datetime(merged["T_REC"])
        merged = merged.dropna(subset=["T_REC_DT", "HARPNUM"])
        if merged.empty:
            print(f"Son {lookback} saatte geçerli T_REC bulunamadı.")
            continue

        latest_time = merged["T_REC_DT"].max()
        print(f"Bulunan en son dolu zaman dilimi: {latest_time}")
        return latest_time.to_pydatetime() if hasattr(latest_time, "to_pydatetime") else latest_time

    return None


def fetch_history_for_harpnum(client, harpnum: int, reference_time: datetime, target_history_hours: int = 72) -> pd.DataFrame:
    start_dt = reference_time - timedelta(hours=target_history_hours)
    start_str = to_jsoc_tai_string(start_dt)
    query = f"hmi.sharp_720s_nrt[{harpnum}][{start_str}/{target_history_hours}h@12m]"
    print(f"\n{target_history_hours} saatlik sorgu (HARPNUM={harpnum}): {query}")
    return safe_query(client, query, QUERY_KEYS)


def standardize_and_clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.lower() for c in df.columns]
    df["t_rec_dt"] = parse_t_rec_to_datetime(df["t_rec"])
    df["harpnum"] = pd.to_numeric(df["harpnum"], errors="coerce")

    numeric_cols = [
        "r_value", "totusjh", "totbsq", "totpot", "totusjz", "absnjzh",
        "savncpp", "usflux", "totfz", "meanpot", "epsx", "epsy", "epsz",
        "meanshr", "shrgt45", "meangam", "meangbt", "meangbz", "meangbh",
        "meanjzh", "totfy", "meanjzd", "meanalp", "totfx",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["fetched_at_utc"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    df = df.dropna(subset=["harpnum", "t_rec", "t_rec_dt"])
    df["harpnum"] = df["harpnum"].astype(int)
    df = df.drop_duplicates(subset=["harpnum", "t_rec"], keep="last")
    df = df.sort_values(["harpnum", "t_rec_dt"]).reset_index(drop=True)
    return df


def run_history_fetch(
    csv_path: str = "veriler_72saat.csv",
    harpnums: list[int] | None = None,
    target_history_hours: int = 72,
    primary_hours: int = 2,
    fallback_hours: int = 6,
    sleep_between_requests: float = 1.0,
) -> Path | None:
    if harpnums is None:
        harpnums = get_active_harpnums(primary_hours=primary_hours, fallback_hours=fallback_hours)

    if not harpnums:
        print("HARPNUM listesi boş.")
        return None

    client = create_client()
    latest_time = get_latest_non_null_timeslot(
        client,
        harpnums,
        primary_hours=primary_hours,
        fallback_hours=fallback_hours,
        sleep_between_requests=sleep_between_requests,
    )
    if latest_time is None:
        print("Verilen HARPNUM listesi için en son dolu zaman dilimi bulunamadı.")
        return None

    print(f"\nReferans zaman: {latest_time}")
    all_frames = []
    for harpnum in harpnums:
        try:
            df = fetch_history_for_harpnum(client, harpnum, latest_time, target_history_hours=target_history_hours)
            if df.empty:
                print(f"HARPNUM={harpnum} için {target_history_hours} saatlik veri bulunamadı.")
            else:
                print(f"HARPNUM={harpnum} için çekilen kayıt sayısı: {len(df)}")
                all_frames.append(df)
        except Exception as exc:
            print(f"[Hata] HARPNUM={harpnum} için veri çekilemedi: {exc}")
        time.sleep(sleep_between_requests)

    if not all_frames:
        print("Hiç veri çekilemedi.")
        return None

    final_df = pd.concat(all_frames, ignore_index=True)
    final_df = standardize_and_clean(final_df)
    out_path = Path(csv_path)
    final_df.to_csv(out_path, index=False, encoding="utf-8")

    print("\nİşlem tamamlandı.")
    print(f"Toplam kayıt: {len(final_df)}")
    print(f"Kaydedilen dosya: {out_path}")
    print("\nİlk 5 satır:")
    print(final_df.head())
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Aktif HARPNUM'lar için geçmiş SHARP verisini çeker.")
    parser.add_argument("--csv-path", default="veriler_72saat.csv")
    parser.add_argument("--target-history-hours", type=int, default=72)
    parser.add_argument("--primary-hours", type=int, default=2)
    parser.add_argument("--fallback-hours", type=int, default=6)
    parser.add_argument("--sleep-between-requests", type=float, default=1.0)
    args = parser.parse_args()
    run_history_fetch(
        csv_path=args.csv_path,
        target_history_hours=args.target_history_hours,
        primary_hours=args.primary_hours,
        fallback_hours=args.fallback_hours,
        sleep_between_requests=args.sleep_between_requests,
    )


if __name__ == "__main__":
    main()

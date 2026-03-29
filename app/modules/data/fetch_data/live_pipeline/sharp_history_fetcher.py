from __future__ import annotations
import time
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd

from live_pipeline.sharp_constants import SharpClient, SharpConstants

class SharpHistoryFetcher:
    def __init__(self, client: SharpClient, sleep_between_requests: float = 1.0):
        self.client = client
        self.sleep_time = sleep_between_requests

    def _get_latest_non_null_timeslot(self, harpnums: list[int], primary_hours: int, fallback_hours: int) -> datetime | None:
        for lookback in [primary_hours, fallback_hours]:
            collected = []
            for harpnum in harpnums:
                query = self.client.build_nrt_query(hours=lookback, harpnum=harpnum)
                df = self.client.safe_query(query, SharpConstants.BASE_KEYS)
                if not df.empty:
                    collected.append(df)
                time.sleep(self.sleep_time)
            
            if not collected:
                continue

            merged = pd.concat(collected, ignore_index=True)
            merged["T_REC_DT"] = self.client.parse_t_rec_to_datetime(merged["T_REC"])
            merged = merged.dropna(subset=["T_REC_DT", "HARPNUM"])
            
            if not merged.empty:
                latest_time = merged["T_REC_DT"].max()
                return latest_time.to_pydatetime() if hasattr(latest_time, "to_pydatetime") else latest_time
        return None

    def _standardize_and_clean(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df.columns = [c.lower() for c in df.columns]
        df["t_rec_dt"] = self.client.parse_t_rec_to_datetime(df["t_rec"])
        df["harpnum"] = pd.to_numeric(df["harpnum"], errors="coerce")

        numeric_cols = SharpConstants.FEATURES_24
        for col in numeric_cols:
            col_lower = col.lower()
            if col_lower in df.columns:
                df[col_lower] = pd.to_numeric(df[col_lower], errors="coerce")

        df["fetched_at_utc"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        df = df.dropna(subset=["harpnum", "t_rec", "t_rec_dt"])
        df["harpnum"] = df["harpnum"].astype(int)
        df = df.drop_duplicates(subset=["harpnum", "t_rec"], keep="last")
        return df.sort_values(["harpnum", "t_rec_dt"]).reset_index(drop=True)

    def fetch_history(self, harpnums: list[int], output_path: Path, target_hours: int = 72, primary_hours: int = 2, fallback_hours: int = 6) -> Path | None:
        latest_time = self._get_latest_non_null_timeslot(harpnums, primary_hours, fallback_hours)
        if latest_time is None:
            print("Verilen HARPNUM listesi için en son dolu zaman dilimi bulunamadı.")
            return None

        all_frames = []
        for harpnum in harpnums:
            try:
                start_dt = latest_time - timedelta(hours=target_hours)
                start_str = self.client.to_jsoc_tai_string(start_dt)
                query = f"hmi.sharp_720s_nrt[{harpnum}][{start_str}/{target_hours}h@12m]"
                
                df = self.client.safe_query(query, SharpConstants.QUERY_KEYS)
                if not df.empty:
                    all_frames.append(df)
            except Exception as exc:
                print(f"[Hata] HARPNUM={harpnum} için veri çekilemedi: {exc}")
            time.sleep(self.sleep_time)

        if not all_frames:
            print("Hiç veri çekilemedi.")
            return None

        final_df = pd.concat(all_frames, ignore_index=True)
        final_df = self._standardize_and_clean(final_df)
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        final_df.to_csv(output_path, index=False, encoding="utf-8")
        print(f"✅ Toplam {len(final_df)} kayıt {output_path} dosyasına kaydedildi.")
        return output_path
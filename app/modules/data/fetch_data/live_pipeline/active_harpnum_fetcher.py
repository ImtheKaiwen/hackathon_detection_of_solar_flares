from __future__ import annotations
import pandas as pd
from live_pipeline.sharp_constants import SharpClient

class ActiveHarpnumFetcher:
    def __init__(self, client: SharpClient):
        self.client = client
        self.keys = ["HARPNUM", "T_REC"]

    def _get_latest_valid_timeslot(self, df: pd.DataFrame) -> tuple[pd.Timestamp | None, pd.DataFrame]:
        temp = df.copy()
        temp["T_REC_DT"] = self.client.parse_t_rec_to_datetime(temp["T_REC"])
        temp = temp.dropna(subset=["T_REC_DT", "HARPNUM"])
        
        if temp.empty:
            return None, pd.DataFrame()

        latest_time = temp["T_REC_DT"].max()
        latest_df = temp[temp["T_REC_DT"] == latest_time].copy()
        return latest_time, latest_df

    def fetch(self, primary_hours: int = 2, fallback_hours: int = 6) -> list[int]:
        query = self.client.build_nrt_query(hours=primary_hours)
        df = self.client.safe_query(query, self.keys)
        latest_time, latest_df = self._get_latest_valid_timeslot(df)

        if latest_df.empty:
            print(f"\n⚠️ {primary_hours} saat içinde veri yok → {fallback_hours} saate geçiliyor")
            query = self.client.build_nrt_query(hours=fallback_hours)
            df = self.client.safe_query(query, self.keys)
            latest_time, latest_df = self._get_latest_valid_timeslot(df)
            
            if latest_df.empty:
                print(f"❌ {fallback_hours} saat içinde de veri bulunamadı")
                return []

        harpnums = pd.to_numeric(latest_df["HARPNUM"], errors="coerce").dropna().astype(int).unique().tolist()
        harpnums.sort()
        
        print(f"\n📌 En son dolu zaman dilimi: {latest_time}")
        print(f"📌 Aktif HARPNUM listesi: {harpnums} (Toplam: {len(harpnums)})")
        return harpnums
from __future__ import annotations

import socket
import time
from datetime import datetime, timedelta
from typing import Iterable

import pandas as pd
import requests

try:
    import drms
except ImportError:  # pragma: no cover
    drms = None


FEATURES_24 = [
    "R_VALUE", "TOTUSJH", "TOTBSQ", "TOTPOT", "TOTUSJZ", "ABSNJZH",
    "SAVNCPP", "USFLUX", "TOTFZ", "MEANPOT", "EPSX", "EPSY", "EPSZ",
    "MEANSHR", "SHRGT45", "MEANGAM", "MEANGBT", "MEANGBZ", "MEANGBH",
    "MEANJZH", "TOTFY", "MEANJZD", "MEANALP", "TOTFX",
]

BASE_KEYS = ["HARPNUM", "T_REC", "NOAA_ARS"]
QUERY_KEYS = BASE_KEYS + FEATURES_24


def create_client():
    if drms is None:
        raise ImportError("drms paketi kurulu değil. Önce 'pip install drms' çalıştırın.")
    return drms.Client()


def to_jsoc_tai_string(dt_obj: datetime) -> str:
    return dt_obj.strftime("%Y.%m.%d_%H:%M:%S_TAI")


def parse_t_rec_to_datetime(series: pd.Series) -> pd.Series:
    return pd.to_datetime(
        series.astype(str).str.replace("_TAI", "", regex=False),
        format="%Y.%m.%d_%H:%M:%S",
        errors="coerce",
    )


def build_nrt_query(hours: int, harpnum: int | None = None, end_time: datetime | None = None) -> str:
    if end_time is None:
        end_time = datetime.utcnow()
    start_dt = end_time - timedelta(hours=hours)
    start_str = to_jsoc_tai_string(start_dt)
    harp_part = "[]" if harpnum is None else f"[{harpnum}]"
    return f"hmi.sharp_720s_nrt{harp_part}[{start_str}/{hours}h@12m]"


def safe_query(client, query: str, keys: Iterable[str], retries: int = 3) -> pd.DataFrame:
    last_error = None

    caught_errors = [
        requests.exceptions.RequestException,
        ConnectionError,
        TimeoutError,
        socket.timeout,
        OSError,
    ]
    if drms is not None and hasattr(drms, "DrmsQueryError"):
        caught_errors.append(drms.DrmsQueryError)

    for attempt in range(1, retries + 1):
        try:
            df = client.query(query, key=",".join(keys))
            if df is None:
                return pd.DataFrame()
            return df
        except tuple(caught_errors) as exc:
            last_error = exc
            print(f"[Uyarı] Sorgu hatası ({attempt}/{retries}): {exc}")
            time.sleep(2)
        except Exception as exc:  # pragma: no cover
            last_error = exc
            print(f"[Uyarı] Beklenmeyen hata ({attempt}/{retries}): {exc}")
            time.sleep(2)

    print(f"[Hata] Sorgu başarısız oldu: {last_error}")
    return pd.DataFrame()

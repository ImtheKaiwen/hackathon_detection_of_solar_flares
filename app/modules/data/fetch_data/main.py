import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from sharp_pipeline.fetch_sharp_history import run_history_fetch
from sharp_pipeline.active_harpnums import get_active_harpnums
from sharp_pipeline.split_hourly_csv import run_split
from sharp_pipeline.fill_missing_features import run_fill_missing_features


def main():
    print("Pipeline başlatılıyor...")

    harpnums = get_active_harpnums()

    output_csv = run_history_fetch(
        harpnums=harpnums,
        csv_path="veriler_72saat.csv",
    )

    if output_csv is not None:
        filled_csv = run_fill_missing_features(
            input_csv=str(output_csv),
            output_csv="veriler_72saat_filled.csv",
        )

        run_split(
            input_csv=str(filled_csv),
            output_dir="harpnum_csvler",
            hours=60,
        )

    print("Pipeline tamamlandı.")


if __name__ == "__main__":
    main()
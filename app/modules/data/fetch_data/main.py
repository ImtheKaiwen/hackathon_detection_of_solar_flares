import sys
from pathlib import Path
from shutil import copy2

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_ROOT = PROJECT_ROOT.parent
SRC_PATH = PROJECT_ROOT / "src"
CLEAN_DATA_DIR = DATA_ROOT / "clean_data"
RAW_OUTPUT_CSV = PROJECT_ROOT / "veriler_72saat.csv"
FILLED_OUTPUT_CSV = CLEAN_DATA_DIR / "veriler_72saat_filled.csv"
HARPNUM_SPLIT_DIR = PROJECT_ROOT / "harpnum_csvler"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from sharp_pipeline.fetch_sharp_history import run_history_fetch
from sharp_pipeline.active_harpnums import get_active_harpnums
from sharp_pipeline.split_hourly_csv import run_split
from sharp_pipeline.fill_missing_features import run_fill_missing_features


def main():
    print("Pipeline başlatılıyor...")
    CLEAN_DATA_DIR.mkdir(parents=True, exist_ok=True)

    harpnums = get_active_harpnums()

    output_csv = run_history_fetch(
        harpnums=harpnums,
        csv_path=str(RAW_OUTPUT_CSV),
    )

    if output_csv is not None:
        filled_csv = run_fill_missing_features(
            input_csv=str(output_csv),
            output_csv=str(FILLED_OUTPUT_CSV),
        )

        # Güvenli yol: fonksiyon farklı bir konuma yazarsa dosyayı hedefe kopyala.
        filled_csv_path = Path(filled_csv)
        if filled_csv_path.resolve() != FILLED_OUTPUT_CSV.resolve():
            copy2(filled_csv_path, FILLED_OUTPUT_CSV)

        run_split(
            input_csv=str(FILLED_OUTPUT_CSV),
            output_dir=str(HARPNUM_SPLIT_DIR),
            hours=60,
        )

        print(f"Doldurulmuş veri dosyası: {FILLED_OUTPUT_CSV}")

    print("Pipeline tamamlandı.")


if __name__ == "__main__":
    main()
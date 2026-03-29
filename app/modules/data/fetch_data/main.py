import sys
from pathlib import Path

# Yolları belirliyoruz
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_ROOT = PROJECT_ROOT.parent 
SRC_PATH = PROJECT_ROOT / "live_pipeline"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from live_pipeline.sharp_constants import SharpClient
from live_pipeline.active_harpnum_fetcher import ActiveHarpnumFetcher
from live_pipeline.sharp_history_fetcher import SharpHistoryFetcher
from live_pipeline.missing_feature_filler import MissingFeatureFiller
from live_pipeline.hourly_data_splitter import HourlyDataSplitter

class SharpDataPipeline:
    def __init__(self):
        # Yollar
        self.clean_data_dir = DATA_ROOT / "clean_data"
        self.raw_output_csv = self.clean_data_dir / "data/veriler_72saat.csv"
        self.filled_output_csv = self.clean_data_dir / "data/veriler_72saat_filled.csv"
        self.harpnum_split_dir = self.clean_data_dir / "data/harpnum_csvler"
        
        # Sınıf Örnekleri (Instances)
        self.client = SharpClient()
        self.active_fetcher = ActiveHarpnumFetcher(self.client)
        self.history_fetcher = SharpHistoryFetcher(self.client)
        self.feature_filler = MissingFeatureFiller()
        self.data_splitter = HourlyDataSplitter()

    def run(self):
        print("Pipeline başlatılıyor...\n")
        self.clean_data_dir.mkdir(parents=True, exist_ok=True)

        print("--- 1. Adım: Aktif HARPNUM'lar Çekiliyor ---")
        harpnums = self.active_fetcher.fetch()
        if not harpnums:
            print("Aktif HARPNUM bulunamadı. Pipeline durduruluyor.")
            return

        print("\n--- 2. Adım: Geçmiş SHARP Verisi Çekiliyor ---")
        output_csv = self.history_fetcher.fetch_history(
            harpnums=harpnums,
            output_path=self.raw_output_csv,
            target_hours=72
        )
        if output_csv is None:
            print("Veri çekilemedi. Pipeline durduruluyor.")
            return

        print("\n--- 3. Adım: Eksik Özellikler Dolduruluyor ---")
        filled_csv_path = self.feature_filler.process(
            input_csv=output_csv,
            output_csv=self.filled_output_csv
        )

        print("\n--- 4. Adım: HARPNUM Bazlı Saatlik CSV'lere Bölünüyor ---")
        self.data_splitter.split(
            input_csv=filled_csv_path,
            output_dir=self.harpnum_split_dir,
            hours=60
        )

        print("\nPipeline başarıyla tamamlandı!")

if __name__ == "__main__":
    pipeline = SharpDataPipeline()
    pipeline.run()
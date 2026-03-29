# Notebook'tan Çıkarılmış Python Mimarisi

Bu klasör, `deneme2.ipynb` notebookundaki kodların çalışır bir Python proje yapısına dönüştürülmüş halidir. Notebook'taki üç ana adım korunmuştur:

1. Aktif HARPNUM listesini bulma
2. Bu HARPNUM'lar için geçmiş SHARP verisini çekip CSV üretme
3. Master CSV dosyasını HARPNUM bazlı ayrı CSV'lere bölme

## Klasör yapısı

```text
notebook_py_mimari/
├── main.py
├── requirements.txt
├── README.md
└── src/
    └── sharp_pipeline/
        ├── __init__.py
        ├── common.py
        ├── active_harpnums.py
        ├── fetch_sharp_history.py
        └── split_hourly_csv.py
```

## Kurulum

```bash
pip install -r requirements.txt
```

## Çalıştırma

### Tek tek modüller

```bash
PYTHONPATH=src python -m sharp_pipeline.active_harpnums
PYTHONPATH=src python -m sharp_pipeline.fetch_sharp_history
PYTHONPATH=src python -m sharp_pipeline.split_hourly_csv --input-csv veriler_72saat.csv
```

### Baştan sona akış

```bash
PYTHONPATH=src python main.py
```

## Not

- Notebook içindeki `harpnums` değişken bağımlılığı kaldırıldı.
- Kod tekrarları azaltıldı ve ortak yardımcı fonksiyonlar `common.py` içine taşındı.
- Komut satırı argümanları eklendiği için saat aralıkları ve çıktı yolları daha kolay değiştirilebilir.

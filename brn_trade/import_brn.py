import sqlite3
import pandas as pd
from pathlib import Path
from tqdm import tqdm
import time
from datetime import datetime

DB_PATH = r"C:\sqlite\brn.db"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS oil_prices (
    ts INTEGER PRIMARY KEY,
    open REAL NOT NULL,
    high REAL NOT NULL,
    low  REAL NOT NULL,
    close REAL NOT NULL,
    volume REAL
);
"""
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(CREATE_TABLE_SQL)
    conn.commit()
    conn.close()

def load_brn_file(path):
    start_time = time.time()
    print(f"    ▶ Начало обработки: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        df = pd.read_csv(
            path,
            sep=';',
            header=None,
            names=['DATE', 'TIME', 'OPEN', 'HIGH', 'LOW', 'CLOSE', 'VOLUME'],
            dtype=str
        )

        df = df[df['DATE'].str.isdigit() & df['TIME'].str.isdigit()]

        df['ts'] = df.apply(lambda row: int("20" + row['DATE'] + row['TIME'][:4]), axis=1)
        df['open'] = df['OPEN'].astype(float)
        df['high'] = df['HIGH'].astype(float)
        df['low']  = df['LOW'].astype(float)
        df['close'] = df['CLOSE'].astype(float)
        df['volume'] = df['VOLUME'].astype(float)

        df = df[['ts', 'open', 'high', 'low', 'close', 'volume']]

        total_rows = len(df)
        inserted = 0
        skipped = 0

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            for i, row in enumerate(df.itertuples(index=False), start=1):
                try:
                    cursor.execute(
                        "INSERT INTO oil_prices (ts, open, high, low, close, volume) VALUES (?, ?, ?, ?, ?, ?)",
                        row
                    )
                    inserted += 1
                except sqlite3.IntegrityError:
                    skipped += 1

                if i % 1000 == 0 or i == total_rows:
                    print(f"    → {i}/{total_rows} строк обработано...", end='\r')

            conn.commit()

        elapsed = time.time() - start_time
        print(f"\n    ✅ Вставлено: {inserted}, пропущено: {skipped}")
        print(f"    ⏱ Завершено за {elapsed:.2f} сек.")

    except Exception as e:
        print(f"    ❌ Ошибка при обработке файла: {path}")
        print(f"       {type(e).__name__}: {e}")

def load_bz_file(path):
    start_time = time.time()
    print(f"    ▶ Начало обработки: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        df = pd.read_csv(
            path,
            sep=';',
            header=None,
            names=['DATE', 'TIME', 'OPEN', 'HIGH', 'LOW', 'CLOSE', 'VOL'],
            dtype=str
        )

        df = df[df['DATE'].str.isdigit() & df['TIME'].str.isdigit()]


        def convert_ts(row):
            return int("20" + row['DATE'] + row['TIME'][:4])  # YYYYMMDDhhmm

        df['ts'] = df.apply(convert_ts, axis=1)
        df['open'] = df['OPEN'].astype(float)
        df['high'] = df['HIGH'].astype(float)
        df['low']  = df['LOW'].astype(float)
        df['close'] = df['CLOSE'].astype(float)
        df['volume'] = df['VOL'].astype(float)

        df = df[['ts', 'open', 'high', 'low', 'close', 'volume']]

        total_rows = len(df)
        inserted = 0
        skipped = 0

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            for i, row in enumerate(df.itertuples(index=False), start=1):
                try:
                    cursor.execute(
                        "INSERT INTO oil_prices (ts, open, high, low, close, volume) VALUES (?, ?, ?, ?, ?, ?)",
                        row
                    )
                    inserted += 1
                except sqlite3.IntegrityError:
                    skipped += 1

                if i % 1000 == 0 or i == total_rows:
                    print(f"    → {i}/{total_rows} строк обработано...", end='\r')

            conn.commit()

        elapsed = time.time() - start_time
        print(f"\n    ✅ Вставлено: {inserted}, пропущено: {skipped}")
        print(f"    ⏱ Завершено за {elapsed:.2f} сек.")

    except Exception as e:
        print(f"    ❌ Ошибка при обработке файла: {path}")
        print(f"       {type(e).__name__}: {e}")

def preview_brn_file(path, limit=10):
    df = pd.read_csv(
        path,
        sep=';',
        header=None,
        names=['DATE', 'TIME', 'OPEN', 'HIGH', 'LOW', 'CLOSE', 'VOLUME'],
        dtype=str,
        nrows=limit
    )

    # Убираем строки с заголовками или мусором
    df = df[df['DATE'].str.isdigit() & df['TIME'].str.isdigit()]

    def convert_ts(row):
        return int("20" + row['DATE'] + row['TIME'][:4])  # YYYYMMDDHHMM

    df['ts'] = df.apply(convert_ts, axis=1)
    df['open'] = df['OPEN'].astype(float)
    df['high'] = df['HIGH'].astype(float)
    df['low']  = df['LOW'].astype(float)
    df['close'] = df['CLOSE'].astype(float)
    df['volume'] = df['VOLUME'].astype(float)

    df = df[['ts', 'open', 'high', 'low', 'close', 'volume']]
    print(df)

def load_bz_folder(folder_path):
    folder = Path(folder_path)
    files = sorted(folder.glob("BZ_*.csv"))
    total = len(files)

    for idx, file in enumerate(files, start=1):
        print(f"\n📄 Обработка файла {idx} из {total}: {file.name}")
        load_bz_file(str(file))

def load_brn_folder(folder_path):
    folder = Path(folder_path)
    files = sorted(folder.glob("BRN_*.csv"))

    for file in tqdm(files, desc="Импорт BRN-файлов"):
        load_brn_file(file)
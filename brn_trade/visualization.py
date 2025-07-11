import sqlite3
import pandas as pd
import mplfinance as mpf

DB_PATH = r"C:\sqlite\brn.db"

def show_chart(limit=1000):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        f"SELECT ts, open, high, low, close, volume FROM oil_prices ORDER BY ts DESC LIMIT {limit}",
        conn
    )
    conn.close()

    df['ts'] = pd.to_datetime(df['ts'], format='%Y%m%d%H%M')
    df.set_index('ts', inplace=True)

    mpf.plot(df.sort_index(), type='candle', volume=True, style='charles')

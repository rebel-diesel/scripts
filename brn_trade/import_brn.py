import sqlite3

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

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(CREATE_TABLE_SQL)
    conn.commit()
    conn.close()
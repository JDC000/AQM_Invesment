import sqlite3
import pandas as pd
from pathlib import Path
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "DB", "investment.db")

def get_connection():
    return sqlite3.connect(DB_FILE)

def get_available_stocks():
    with get_connection() as conn:
        query = "SELECT DISTINCT symbol FROM market_data"
        rows = conn.execute(query).fetchall()
        return [row[0] for row in rows]

def load_stock_data(symbol, start_date, end_date):
    with get_connection() as conn:
        query = """
        SELECT date, close
        FROM market_data
        WHERE symbol = ?  AND date BETWEEN ? AND ?
        ORDER BY date
        """
        return pd.read_sql_query(query, conn, params=[symbol, str(start_date), str(end_date)], parse_dates=['date'])

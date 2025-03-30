import pandas as pd
import sqlite3
import os
import sys


def run_strategy(df: pd.DataFrame, fenster: int = 50, tolerance: float = 0.01, start_kapital: float = 100000):
    """
    Fibonacci-Retracement-Strategie:
    - Berechnet Fibonacci-Level basierend auf rollierenden Hochs/Tiefs
    - Generiert Kaufsignale, wenn der Kurs nahe dem 38,2%-Level liegt,
      und Verkaufssignale, wenn der Kurs nahe dem 61,8%-Level liegt.
    - Simuliert Trades (alles rein, alles raus) und gibt (final_value, gewinn) zurück.
    """
    df = df.copy()
    df["rolling_max"] = df["close"].rolling(window=fenster).max().shift(1)
    df["rolling_min"] = df["close"].rolling(window=fenster).min().shift(1)
    df["diff"] = df["rolling_max"] - df["rolling_min"]

    df["fib_38"]  = df["rolling_max"] - 0.382 * df["diff"]
    df["fib_62"]  = df["rolling_max"] - 0.618 * df["diff"]

    def get_signal(row):
        if pd.isna(row["fib_38"]) or pd.isna(row["fib_62"]):
            return 0
        if abs(row["close"] - row["fib_38"]) / row["fib_38"] < tolerance:
            return 1
        elif abs(row["close"] - row["fib_62"]) / row["fib_62"] < tolerance:
            return -1
        return 0

    df["signal"] = df.apply(get_signal, axis=1)

    kapital = start_kapital
    position = 0
    for i in range(len(df)):
        preis = df.iloc[i]["close"]
        signal = df.iloc[i]["signal"]
        if signal == 1 and position == 0:
            position = kapital / preis
            kapital = 0
        elif signal == -1 and position > 0:
            kapital = position * preis
            position = 0

    final_value = kapital + position * df.iloc[-1]["close"]
    gewinn = final_value - start_kapital
    return final_value, gewinn

# -------------------------
# Test-Main Fibonacci
# -------------------------
if __name__ == "__main__":
    from common import ensure_close_column, ensure_datetime_index, format_currency
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    BASE_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
    DB_NAME = os.path.join(BASE_DIR, "Datenbank", "DB", "investment.db")

    symbol = "AAPL"
    start_date = "2010-01-01"
    end_date = "2020-12-31"

    try:
        conn = sqlite3.connect(DB_NAME)
        query = """
            SELECT date, close
            FROM market_data
            WHERE symbol = ? AND date BETWEEN ? AND ?
            ORDER BY date
        """
        params = [symbol, start_date, end_date]
        df_db = pd.read_sql_query(query, conn, params=params, parse_dates=["date"])
    except Exception as e:
        print("Fehler beim Laden der Daten:", e)
        sys.exit(1)
    finally:
        conn.close()

    try:
        df_db = ensure_close_column(df_db)
        df_db = ensure_datetime_index(df_db)
    except Exception as e:
        print("Fehler bei der Datenaufbereitung:", e)
        sys.exit(1)

    start_value = 100000
    end_value, profit = run_strategy(df_db, fenster=50, tolerance=0.01, start_kapital=start_value)
    percent_change = (end_value - start_value) / start_value * 100

    print("Fibonacci-Retracement Strategie:")
    print("Startwert: €" + format_currency(start_value))
    print("Endwert: €" + format_currency(end_value))
    print("Gewinn/Verlust: €" + format_currency(profit))
    print("Prozentuale Veränderung: " + format_currency(percent_change) + " %")

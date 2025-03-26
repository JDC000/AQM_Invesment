import pandas as pd
import sqlite3
import os
import sys

# Gemeinsame Hilfsfunktionen importieren (sollten in common.py definiert sein)
from .common import ensure_close_column, ensure_datetime_index, format_currency

def run_strategy(df: pd.DataFrame, start_kapital: float = 100000):
    """
    Buy and Hold Strategie:
    - Investiert am frühestmöglichen Tag das gesamte Kapital
    - Verkauft am spätestmöglichen Tag
    - Gibt (gesamtwert, gewinn) zurück
    """
    df = df.copy()
    # Signalspalte initialisieren
    df["signal"] = 0
    if not df.empty:
        df.loc[df.index[0], "signal"] = 1   # Kauf
        df.loc[df.index[-1], "signal"] = -1   # Verkauf

    # Simulation der Transaktionen
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

    # Endwert berechnen
    gesamtwert = kapital + position * df.iloc[-1]["close"]
    gewinn = gesamtwert - start_kapital
    return gesamtwert, gewinn

# -------------------------
# Test-Main Buy and Hold
# -------------------------
if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    # Passe den Pfad an: z. B. eine Ebene nach oben in "Datenbank/DB"
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
    end_value, profit = run_strategy(df_db, start_kapital=start_value)
    percent_change = (end_value - start_value) / start_value * 100

    print("Buy and Hold Strategie:")
    print("Startwert: €" + format_currency(start_value))
    print("Endwert: €" + format_currency(end_value))
    print("Gewinn/Verlust: €" + format_currency(profit))
    print("Prozentuale Veränderung: " + format_currency(percent_change) + " %")

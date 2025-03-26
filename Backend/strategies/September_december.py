import pandas as pd
import sqlite3
import os
import sys
from common import ensure_close_column, ensure_datetime_index, format_currency

def run_strategy(df: pd.DataFrame, start_kapital: float = 100000):
    """
    Buy-September / Sell-December Strategie:
    - Setzt am ersten Handelstag im September ein Kaufsignal und
      am ersten Handelstag im Dezember ein Verkaufssignal.
    - Simuliert Trades (alles rein, alles raus) und gibt (gesamtwert, gewinn) zurück.
    """
    df = df.copy()
    # Sicherstellen, dass der Index ein DatetimeIndex ist und nur das Datum enthält
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
    df.index = df.index.normalize()  # Entfernt Zeitinformationen, sodass nur das Datum übrig bleibt

    # Signale initialisieren
    df["signal"] = 0
    grouped = df.groupby([df.index.year, df.index.month])
    for (year, month), group in grouped:
        first_day = group.index.min()
        # Debug-Ausgabe – bei Bedarf aktivieren:
        # print(f"Jahr: {year}, Monat: {month}, erster Tag: {first_day}")
        if month == 9:
            df.loc[first_day, "signal"] = 1
        elif month == 12:
            df.loc[first_day, "signal"] = -1

    # Simulation der Transaktionen
    kapital = start_kapital
    position = 0
    for i in range(len(df)):
        preis = df.iloc[i]["close"]
        signal = df.iloc[i]["signal"]
        if signal == 1 and position == 0:
            # Kaufsignal: Volles Kapital investieren
            position = kapital / preis
            kapital = 0
        elif signal == -1 and position > 0:
            # Verkaufssignal: Position liquidieren
            kapital = position * preis
            position = 0

    gesamtwert = kapital + position * df.iloc[-1]["close"]
    gewinn = gesamtwert - start_kapital
    return gesamtwert, gewinn

# -------------------------
# Test-Main Buy September / Sell December
# -------------------------
if __name__ == "__main__":
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
    end_value, profit = run_strategy(df_db, start_kapital=start_value)
    percent_change = (end_value - start_value) / start_value * 100

    print("Buy-September / Sell-December Strategie:")
    print("Startwert: €" + format_currency(start_value))
    print("Endwert: €" + format_currency(end_value))
    print("Gewinn/Verlust: €" + format_currency(profit))
    print("Prozentuale Veränderung: " + format_currency(percent_change) + " %")

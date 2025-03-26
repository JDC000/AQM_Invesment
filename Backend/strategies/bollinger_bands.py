import pandas as pd

def run_strategy(df: pd.DataFrame, window: int = 20, num_std: int = 2, start_kapital: float = 100000):
    """
    Bollinger-Bands-Strategie:
    - Berechnet Bollinger-Bands (gleitender Durchschnitt + Standardabweichung)
    - Generiert Signale: 1 = Kaufsignal (close unter unterem Band), -1 = Verkaufssignal (close über oberem Band)
    - Simuliert Trades (alles rein, alles raus) und berechnet die Equity-Kurve
    - Gibt (final_value, profit) zurück
    """
    df = df.copy()
    # Bollinger-Bands berechnen
    df["MA"] = df["close"].rolling(window=window).mean()
    df["std"] = df["close"].rolling(window=window).std()
    df["upper_band"] = df["MA"] + num_std * df["std"]
    df["lower_band"] = df["MA"] - num_std * df["std"]

    # Signale: Kaufen = 1, Verkaufen = -1
    df["signal"] = 0
    df.loc[df["close"] < df["lower_band"], "signal"] = 1
    df.loc[df["close"] > df["upper_band"], "signal"] = -1

    # Trade-Simulation
    kapital = start_kapital
    position = 0
    equity_curve = []
    for i in range(len(df)):
        preis = df.iloc[i]["close"]
        signal = df.iloc[i]["signal"]
        if signal == 1 and position == 0:
            # Alles rein: Kauf
            position = kapital / preis
            kapital = 0
        elif signal == -1 and position > 0:
            # Alles raus: Verkauf
            kapital = position * preis
            position = 0
        equity_curve.append(kapital + position * preis)

    final_value = equity_curve[-1] if equity_curve else start_kapital
    profit = final_value - start_kapital

    return final_value, profit



# -------------------------
# Test-Main in der Strategie
# -------------------------
if __name__ == "__main__":
    import sys
    import os
    import sqlite3
    import pandas as pd

    # Importiere die gemeinsamen Hilfsfunktionen
    from common import ensure_close_column, ensure_datetime_index, format_currency

    # Passe den Pfad an: eine Ebene nach oben und dann in "Datenbank/DB"
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    BASE_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
    DB_NAME = os.path.join(BASE_DIR, "Datenbank", "DB", "investment.db")
    
    # Definition des Symbols und Zeitraums
    symbol = "AAPL"  # Beispiel-Symbol – passe dies ggf. an
    start_date = "2010-01-01"
    end_date = "2020-12-31"
    
    # Verbindung zur SQLite-Datenbank herstellen und Daten laden
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
        print("Fehler beim Laden der Daten aus der Datenbank:", e)
        sys.exit(1)
    finally:
        conn.close()
    
    # Sicherstellen, dass das DataFrame die Spalte 'close' enthält und der Index ein DatetimeIndex ist
    try:
        df_db = ensure_close_column(df_db)
        df_db = ensure_datetime_index(df_db)
    except Exception as e:
        print("Fehler bei der Datenaufbereitung:", e)
        sys.exit(1)
    
    # Strategie ausführen
    start_value = 100000
    final_value, profit = run_strategy(df_db, start_kapital=start_value)
    percent_change = (final_value - start_value) / start_value * 100

    # Ausgabe in der Konsole mit formatierter Währung
    print("Startwert: €" + format_currency(start_value))
    print("Endwert: €" + format_currency(final_value))
    print("Gewinn/Verlust: €" + format_currency(profit))
    print("Prozentuale Veränderung: " + format_currency(percent_change) + " %")

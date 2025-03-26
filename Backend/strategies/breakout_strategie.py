import sqlite3
import pandas as pd
import os

def run_strategy(df: pd.DataFrame, fenster: int = 20, start_kapital: float = 100000):
    """
    Breakout-Strategie:
    - Kauft, wenn der Schlusskurs das bisherige Hoch (letzte 'fenster' Tage, um 1 Tag verschoben) überschreitet
    - Verkauft, wenn der Schlusskurs das bisherige Tief unterschreitet
    - Simuliert Trades (alles rein, alles raus) und berechnet die Equity-Kurve
    - Gibt (final_value, gewinn) zurück
    """
    df = df.copy()
    
    # Berechne Highest und Lowest der letzten 'fenster' Tage (um 1 Tag verschoben)
    df["highest"] = df["close"].rolling(window=fenster).max().shift(1)
    df["lowest"] = df["close"].rolling(window=fenster).min().shift(1)
    
    # Generiere Signale: 1 = Kaufsignal, -1 = Verkaufssignal
    df["signal"] = 0
    df.loc[df["close"] > df["highest"], "signal"] = 1
    df.loc[df["close"] < df["lowest"], "signal"] = -1
    
    # Trade-Simulation: Alles rein/raus
    kapital = start_kapital
    position = 0
    equity_curve = []
    
    for i in range(len(df)):
        preis = df.iloc[i]["close"]
        signal = df.iloc[i]["signal"]
        if signal == 1 and position == 0:
            # Kaufe: Alle Mittel einsetzen
            position = kapital / preis
            kapital = 0
        elif signal == -1 and position > 0:
            # Verkaufe: Position liquidieren
            kapital = position * preis
            position = 0
        equity_curve.append(kapital + position * preis)
    
    final_value = equity_curve[-1] if equity_curve else start_kapital
    gewinn = final_value - start_kapital
    return final_value, gewinn

# -------------------------
# Test-Main in der Strategie
# -------------------------
if __name__ == "__main__":
    import sys
    # Importiere die gemeinsamen Hilfsfunktionen (müssen im Modul common.py liegen)
    from common import ensure_close_column, ensure_datetime_index, format_currency

    # Passe den Pfad an: eine Ebene nach oben und dann in "Datenbank/DB"
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    BASE_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
    DB_NAME = os.path.join(BASE_DIR, "Datenbank", "DB", "investment.db")
    
    # Definition des Symbols und Zeitraums
    symbol = "AAPL"  # Beispiel-Symbol – anpassen, falls nötig
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
    
    # Datenaufbereitung: Sicherstellen, dass 'close' vorhanden ist und der Index ein DatetimeIndex ist
    try:
        df_db = ensure_close_column(df_db)
        df_db = ensure_datetime_index(df_db)
    except Exception as e:
        print("Fehler bei der Datenaufbereitung:", e)
        sys.exit(1)
    
    # Strategie ausführen
    start_value = 100000
    final_value, gewinn = run_strategy(df_db, fenster=20, start_kapital=start_value)
    percent_change = (final_value - start_value) / start_value * 100

    # Ausgabe in der Konsole mit formatierter Währung
    print("Startwert: €" + format_currency(start_value))
    print("Endwert: €" + format_currency(final_value))
    print("Gewinn/Verlust: €" + format_currency(gewinn))
    print("Prozentuale Veränderung: " + format_currency(percent_change) + " %")

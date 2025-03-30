import sqlite3
import pandas as pd
import yfinance as yf
import time
import os

# Name der SQLite-Datenbank
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_dir = os.path.join(BASE_DIR, "DB")
if not os.path.exists(db_dir):
    os.makedirs(db_dir)

DB_NAME = os.path.join(db_dir, "investment.db")

# Listen von Aktien, ETFs und Kryptowährungen
stocks = ["AAPL", "MSFT", "AMZN", "GOOGL", "TSLA", "META", "NVDA", "JNJ", "V", "JPM",
          "WMT", "PG", "DIS", "MA", "HD", "BAC", "XOM", "PFE", "KO", "CSCO",
          "PEP", "INTC", "MRK", "ABT", "CMCSA", "ADBE", "NFLX", "NKE", "ORCL", "T",
          "CRM", "LLY", "MCD", "AMD", "IBM", "HON", "UNH", "CVX", "BA", "COST",
          "AVGO", "TXN", "QCOM", "AMGN", "MDT", "LIN", "UPS", "NEE", "PM", "SPGI"]
etfs = [
    "XFI", "XIT", "XLB", "XLE", "XLF", "XLI", "XLP", "XLU", "XLV", "XLY", "XSE", "VT"
]
cryptos = [
    "BNB", "XRP", "SOL", "DOT", "LTC",
    "USDC", "LINK", "BCH", "XLM", "UNI", "ATOM", "TRX",
    "ETC", "NEAR", "XMR", "VET", "EOS", "FIL", "CRO", "DAI", "DASH", "ENJ"
]

# Automatische Erstellung der Datenbank
def create_database():
    """Erstellt die SQLite-Datenbank, falls sie noch nicht existiert."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS market_data (
            asset_type TEXT,
            symbol TEXT,
            date TEXT,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume REAL,
            PRIMARY KEY (asset_type, symbol, date)
        )
    """)
    conn.commit()
    conn.close()

def fetch_yfinance_data(symbol, asset_type, start="2010-01-01", end="2023-12-31"):
    """Holt historische Daten von Yahoo Finance und stellt sicher, dass das Datum korrekt formatiert ist."""
    try:
        df = yf.download(symbol, start=start, end=end, progress=False)
        if df.empty:
            print(f"Keine Daten für {symbol} gefunden.")
            return None

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)

        print(f"Korrigierte Spalten für {symbol}: {df.columns}")

        df.reset_index(inplace=True)
        df.rename(columns={"Date": "date", "Open": "open", "High": "high",
                           "Low": "low", "Close": "close", "Volume": "volume"}, inplace=True)

        df["date"] = df["date"].astype(str)  # als TEXT speichern
        df["asset_type"] = asset_type
        df["symbol"] = symbol

        return df

    except Exception as e:
        print(f"Fehler beim Abrufen von {symbol}: {e}")
        return None

def save_to_database(data):
    """Speichert Daten in der SQLite-Datenbank, falls sie existieren."""
    if data is None or data.empty:
        print("Keine Daten zum Speichern vorhanden.")
        return

    # Debugging: Überprüfen, ob alle Spalten vorhanden sind
    print("Spalten in DataFrame vor Speicherung:", list(data.columns))

    conn = sqlite3.connect(DB_NAME)
    data.to_sql("market_data", conn, if_exists="append", index=False)
    conn.commit()
    conn.close()
    print(f"Daten erfolgreich gespeichert für {data['symbol'][0]}")

def get_data_from_db(asset_type, symbol, start_date="2010-01-01", end_date="2020-12-31"):
    """Holt gespeicherte Daten aus der Datenbank."""
    conn = sqlite3.connect(DB_NAME)
    query = f"""
        SELECT * FROM market_data
        WHERE asset_type = '{asset_type}' AND symbol = '{symbol}'
        AND date BETWEEN '{start_date}' AND '{end_date}'
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

if __name__ == "__main__":
    # Falls die Datenbank bereits existiert, löschen wir sie vorab
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
        print(f"Alte Datenbank {DB_NAME} wurde gelöscht.")

    # Datenbank neu erstellen
    create_database()

    # Aktien & ETFs abrufen
    for symbol in stocks + etfs:
        print(f"Abrufen von Daten für {symbol}...")
        df = fetch_yfinance_data(symbol, "Stock/ETF")
        save_to_database(df)
        time.sleep(2)  # API-Limit vermeiden

    # Kryptowährungen abrufen
    for symbol in cryptos:
        print(f"Abrufen von Daten für Kryptowährung: {symbol}...")
        df = fetch_yfinance_data(symbol, "Crypto")
        save_to_database(df)
        time.sleep(2)  # API-Limit vermeiden

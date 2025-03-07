
import sqlite3
import pandas as pd
from alpha_vantage.timeseries import TimeSeries
from alpha_vantage.cryptocurrencies import CryptoCurrencies

# API-Schlüssel für Alpha Vantage
API_KEY = "LY52UKSUI6ZO5C7A"

# Name der SQLite-Datenbank
DB_NAME = "investment.db"

def fetch_stock_etf_data(symbol, start_year=2010, end_year=2020):
    """Holt historische Aktien- und ETF-Daten von Alpha Vantage."""
    ts = TimeSeries(key=API_KEY, output_format="pandas")
    data, meta_data = ts.get_daily(symbol=symbol, outputsize="full")

    # Datenformatierung
    data.index = pd.to_datetime(data.index)
    data = data[(data.index >= f"{start_year}-01-01") & (data.index <= f"{end_year}-12-31")]
    data.reset_index(inplace=True)

    # Spaltennamen umbenennen
    data.rename(columns={"date": "Date", "1. open": "Open", "2. high": "High",
                         "3. low": "Low", "4. close": "Close", "5. volume": "Volume"}, inplace=True)
    return data

def fetch_crypto_data(symbol, market="USD"):
    """Holt historische Kryptowährungsdaten von Alpha Vantage."""
    cc = CryptoCurrencies(key=API_KEY, output_format="pandas")
    data, meta_data = cc.get_digital_currency_daily(symbol=symbol, market=market)

    # Datenformatierung
    data.index = pd.to_datetime(data.index)
    data.reset_index(inplace=True)

    # Spaltennamen umbenennen
    data.rename(columns={"date": "Date", "1a. open (USD)": "Open", "2a. high (USD)": "High",
                         "3a. low (USD)": "Low", "4a. close (USD)": "Close", "5. volume": "Volume"}, inplace=True)
    return data

def save_to_database(asset_type, symbol, data):
    """Speichert Daten in der SQLite-Datenbank."""
    conn = sqlite3.connect(DB_NAME)
    data["asset_type"] = asset_type
    data["symbol"] = symbol  # Spalte für den Asset-Typ hinzufügen
    data.to_sql("market_data", conn, if_exists="append", index=False)
    conn.close()

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
    # Liste von Aktien, ETFs und Kryptowährungen
    stocks_etfs = ["AAPL", "TSLA", "SPY"]  # Beispiel: Apple, Tesla, S&P 500 ETF
    cryptos = ["BTC", "ETH", "SOL"]  # Beispiel: Bitcoin, Ethereum, Solana

    # Abruf von Aktien & ETFs
    for symbol in stocks_etfs:
        print(f"Abrufen von Daten für {symbol}...")
        df = fetch_stock_etf_data(symbol)
        save_to_database("Stock/ETF", symbol, df)
        print(f"Daten für {symbol} gespeichert!")

    # Abruf von Kryptowährungen
    for symbol in cryptos:
        print(f"Abrufen von Daten für Kryptowährung: {symbol}...")
        df = fetch_crypto_data(symbol)
        save_to_database("Crypto", symbol, df)
        print(f"Daten für {symbol} gespeichert!")

    # Überprüfung gespeicherter Daten
    print("Daten für AAPL aus der Datenbank:")
    print(get_data_from_db("Stock/ETF", "AAPL").head())

    print("Daten für BTC aus der Datenbank:")
    print(get_data_from_db("Crypto", "BTC").head())




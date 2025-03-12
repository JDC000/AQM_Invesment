
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
    stocks = [
    "AAPL", "MSFT", "AMZN", "GOOGL", "TSLA", "META", "NVDA", "JNJ", "V", "JPM",
    "WMT", "PG", "DIS", "MA", "HD", "BAC", "XOM", "PFE", "KO", "CSCO",
    "PEP", "INTC", "MRK", "ABT", "CMCSA", "ADBE", "NFLX", "NKE", "ORCL", "T",
    "CRM", "LLY", "MCD", "AMD", "IBM", "HON", "UNH", "CVX", "BA", "COST",
    "AVGO", "TXN", "QCOM", "AMGN", "MDT", "LIN", "UPS", "NEE", "PM", "SPGI",
    "GS", "MS", "BLK", "AXP", "BKNG", "NOW", "ISRG", "LMT", "GE", "CAT",
    "MMM", "DE", "F", "GM", "SBUX", "PYPL", "DHR", "GILD", "PLD", "ADP",
    "CI", "MO", "SCHW", "ZTS", "SYK", "MMC", "TJX", "C", "DUK", "BDX",
    "TMO", "LOW", "USB", "RTX", "SLB", "COP", "AMT", "CCI", "CL", "D",
    "SO", "SRE", "ETN", "ECL", "ITW", "APD", "SHW", "FIS", "FISV", "BK",
    "ICE", "CME", "MCO", "SPG", "PSA", "FDX", "EMR", "AON", "MET", "PRU",
    "TRV", "ALL", "AIG", "LRCX", "KLAC", "ADI", "MU", "NXPI", "WDAY", "SNPS",
    "CDNS", "ANSS", "FTNT", "PANW", "ZM", "DOCU", "CRWD", "DDOG", "OKTA", "ZS",
    "TEAM", "MDB", "TWLO", "NET", "SNOW", "U", "SHOP", "SQ", "ROKU", "TTD"
]
  # Beispiel: Apple, Tesla, S&P 500 ETF
    etfs = [
    "CSPX", "ISF", "EIMI", "IUSA", "VGK", "VUSA", "XDWD", "XDEQ", "SPY5", "ZPRS",
    "EQQQ", "IQQQ", "SXR8", "IWDA", "EUNL", "VWRL", "VEUR", "VJPN", "VFEM", "XCS5",
    "XMME", "XESX", "XSPX", "XDUK", "XDJP", "XDEM", "XD9U", "XGGB", "XGSC", "XGEM",
    "XMID", "XSMI", "XDTF", "XFR", "XIT", "XAT", "XNL", "XSE", "XBE", "XFI", "XNO",
    "XLV", "XLY", "XLF", "XLE", "XLB", "XLU", "XLP", "XLI", "XRE", "XDWG", "XEUR",
    "XDUS", "XDGB", "XDEW", "XDWE", "XSX5", "XSX4", "XSX3", "XSX2", "XSX1", "XLRE",
    "XSDJ", "XSTOXX", "XSME", "XJPN", "XEMB", "XEME", "XEMD", "XEMX", "XUSA", "XHKG",
    "XCHN", "XIND", "XBRZ", "XMEX", "XSAU", "XSGP", "XNZL", "XISR", "XTHA", "XPHL",
    "XDWD", "XDJP", "XUSA", "XEUR", "XREU", "XGLO", "XUKX", "XMSCI", "XACWI", "XWO",
    "XIEE", "XETF", "XWLD", "XSUS", "XGER", "XFRA", "XITL", "XUK", "XFDX", "XDX2",
    "XNXE", "XDNQ", "XFTSE", "XFTD", "XFUK", "XEME", "XEMT", "XEFA", "XFEE", "XD5E"
]

    cryptos = [
    "BTC", "ETH", "USDT", "BNB", "XRP", "ADA", "SOL", "DOGE", "DOT", "LTC",
    "USDC", "LINK", "BCH", "XLM", "UNI", "ATOM", "ALGO", "MATIC", "AVAX", "TRX",
    "ETC", "FTT", "NEAR", "XMR", "VET", "EOS", "AAVE", "KSM", "FIL", "XTZ",
    "THETA", "CRO", "DAI", "HBAR", "MKR", "SUSHI", "COMP", "ZEC", "DASH", "ENJ",
    "BAT", "GRT", "CHZ", "YFI", "SNX", "RUNE", "ZIL", "ONT", "QTUM", "OMG",
    "ICX", "STX", "NANO", "BTT", "SC", "ANKR", "RVN", "KAVA", "CEL", "FTM",
    "HNT", "ONE", "LRC", "REN", "BAL", "SRM", "CVC", "OCEAN", "STORJ", "UMA",
    "BAND", "KNC", "REP", "PAXG", "NEXO", "GNO", "AR", "LPT", "RSR", "SXP",
    "ZEN", "WRX", "CKB", "DGB", "COTI", "STMX", "FUN", "MTL", "TRAC", "AKRO",
    "PERP", "ORN", "MLN", "MIR", "ALPHA", "RLC", "ANT", "WNXM", "KEEP", "BADGER",
    "FET", "CTSI", "DIA", "AVA", "POLY", "MANA", "SAND", "AXS", "GALA", "ILV",
    "YGG", "FLOW", "CHR", "UOS", "WAXP", "LOOM", "C98", "XVS", "BAKE", "BEL",
    "TWT", "DODO", "EPS", "AUTO", "ALICE", "DEGO", "LINA", "FARM", "RENBTC", "DIGG",
    "MITH", "DOGE", "SHIB", "ELON", "SAFEMOON", "BABYDOGE", "FLOKI", "KISHU", "AKITA",
    "HOGE", "SAMO", "PIT", "FEG", "HUSKY", "KEANU", "ELD", "KUMA", "SHIBA", "SHIBX",
    "SHIBU"
]
  # Beispiel: Bitcoin, Ethereum, Solana

    # Abruf von Aktien 
    for symbol in stocks:
        print(f"Abrufen von Daten für {symbol}...")
        df = fetch_stock_etf_data(symbol)
        save_to_database("Stock/ETF", symbol, df)
        print(f"Daten für {symbol} gespeichert!")

    # Abruf von ETFs
    for symbol in etfs:
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




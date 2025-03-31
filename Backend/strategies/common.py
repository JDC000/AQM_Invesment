import pandas as pd

def ensure_close_column(df):
    if "close" not in df.columns:
        if "Price" in df.columns:
            df = df.rename(columns={"Price": "close"})
        else:
            raise ValueError("Das DataFrame enthält weder 'close' noch 'Price'")
    return df

def ensure_datetime_index(df):
    if not isinstance(df.index, pd.DatetimeIndex):
        try:
            df.index = pd.to_datetime(df.index)
        except Exception as e:
            raise ValueError("Index konnte nicht in datetime konvertiert werden: " + str(e))
    return df

def calculate_buy_and_hold_performance(df, start_kapital):
    start_price = df.iloc[0]["close"]
    end_price = df.iloc[-1]["close"]
    total = start_kapital * (end_price / start_price)
    percent_gain = (total - start_kapital) / start_kapital * 100
    return total, percent_gain

def filter_stocks(tickers):
    ETFS = {"XFI", "XIT", "XLB", "XLE", "XLF", "XLI", "XLP", "XLU", "XLV", "XLY", "XSE", "VT"}
    CRYPTOS = {"BNB", "XRP", "SOL", "DOT", "LTC",
               "USDC", "LINK", "BCH", "XLM", "UNI", "ATOM", "TRX",
               "ETC", "NEAR", "XMR", "VET", "EOS", "FIL", "CRO", "DAI", "DASH", "ENJ"}
    return [ticker for ticker in tickers if ticker not in ETFS and ticker not in CRYPTOS]


def format_currency(value):
    s = f"{value:,.2f}" 
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return s

def extract_numeric_result(result):
    if isinstance(result, tuple):
        if len(result) == 4:
            return result[2], result[3]
        elif len(result) == 2:
            return result
    raise ValueError("Unbekanntes Rückgabeformat der Strategie.")

def calculate_vt_performance(df,START_CAPITAL):
    initial_price = df.iloc[0]['close']
    final_price = df.iloc[-1]['close']
    final_value = (final_price / initial_price) * START_CAPITAL
    profit = final_value - START_CAPITAL
    percent = (profit / START_CAPITAL) * 100
    return {"final_value": final_value, "profit": profit, "percent": percent}
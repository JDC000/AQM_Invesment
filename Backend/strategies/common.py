import pandas as pd

def ensure_close_column(df):
    """
    Überprüft, ob das DataFrame die Spalte 'close' enthält.
    Falls stattdessen 'Price' vorhanden ist, wird diese umbenannt.
    """
    if "close" not in df.columns:
        if "Price" in df.columns:
            df = df.rename(columns={"Price": "close"})
        else:
            raise ValueError("Das DataFrame enthält weder 'close' noch 'Price'")
    return df

def ensure_datetime_index(df):
    """
    Stellt sicher, dass der Index des DataFrames ein DatetimeIndex ist.
    Falls nicht, wird versucht, den Index in einen DatetimeIndex zu konvertieren.
    """
    if not isinstance(df.index, pd.DatetimeIndex):
        try:
            df.index = pd.to_datetime(df.index)
        except Exception as e:
            raise ValueError("Index konnte nicht in datetime konvertiert werden: " + str(e))
    return df

def calculate_buy_and_hold_performance(df, start_kapital):
    """
    Berechnet die Buy-&-Hold-Performance:
    - Startpreis entspricht dem ersten 'close'-Wert,
    - Endpreis dem letzten 'close'-Wert.
    Es wird der Endkapitalwert sowie der prozentuale Gewinn zurückgegeben.
    """
    start_price = df.iloc[0]["close"]
    end_price = df.iloc[-1]["close"]
    total = start_kapital * (end_price / start_price)
    percent_gain = (total - start_kapital) / start_kapital * 100
    return total, percent_gain

def filter_stocks(tickers):
    """
    Filtert die Tickerliste, sodass nur Aktien (Stocks) enthalten sind.
    Folgende ETFs und Cryptos werden ausgelassen:
      ETFS = {"XFI", "XIT", "XLB", "XLE", "XLF", "XLI", "XLP", "XLU", "XLV", "XLY", "XSE", "VT"}
      CRYPTOS = {"BNB", "XRP", "SOL", "DOT", "LTC", "USDC", "LINK", "BCH", "XLM", "UNI",
                 "ATOM", "TRX", "ETC", "NEAR", "XMR", "VET", "EOS", "FIL", "CRO", "DAI", "DASH", "ENJ"}
    """
    ETFS = {"XFI", "XIT", "XLB", "XLE", "XLF", "XLI", "XLP", "XLU", "XLV", "XLY", "XSE", "VT"}
    CRYPTOS = {"BNB", "XRP", "SOL", "DOT", "LTC",
               "USDC", "LINK", "BCH", "XLM", "UNI", "ATOM", "TRX",
               "ETC", "NEAR", "XMR", "VET", "EOS", "FIL", "CRO", "DAI", "DASH", "ENJ"}
    return [ticker for ticker in tickers if ticker not in ETFS and ticker not in CRYPTOS]


def format_currency(value):
    """
    Formatiert einen Zahlenwert als Währung:
    Tausender werden mit einem Punkt getrennt und die Nachkommastellen mit einem Komma.
    Beispiel: 100000 -> "100.000,00"
    """
    s = f"{value:,.2f}"  # Beispiel: 100,000.00 (englisches Format)
    # Tauschen: Komma -> Temporärmarke, Punkt -> Komma, Temporärmarke -> Punkt
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return s
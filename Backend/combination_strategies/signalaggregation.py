#!/usr/bin/env python
import sys
import os
import pandas as pd
import plotly.graph_objects as go

# Pfad erweitern, damit Module aus dem übergeordneten Verzeichnis gefunden werden
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from Datenbank.api import get_available_stocks, load_stock_data

def filter_stocks(tickers):
    """
    Filtert die Tickerliste, sodass nur Aktien (Stocks) enthalten sind.
    ETFs und Cryptos werden ausgeklammert.
    """
    ETFS = {"XFI", "XIT", "XLB", "XLE", "XLF", "XLI", "XLP", "XLU", "XLV", "XLY", "XSE", "VT"}
    CRYPTOS = {"BNB", "XRP", "SOL", "DOT", "LTC", "USDC", "LINK", "BCH", "XLM", "UNI",
               "ATOM", "TRX", "ETC", "NEAR", "XMR", "VET", "EOS", "FIL", "CRO", "DAI", "DASH", "ENJ"}
    return [ticker for ticker in tickers if ticker not in ETFS and ticker not in CRYPTOS]

def run_strategy_signal_aggregation(df, start_kapital=100000):
    """
    Kombiniert zwei Signale:
      - Strategie A: 50-Tage-SMA – Signal: Kauf, wenn close > SMA50, Verkauf, wenn close < SMA50.
      - Strategie B: Bollinger Bands – Signal: Kauf, wenn close unter dem unteren Band, Verkauf, wenn close über dem oberen Band.
    Das kombinierte Signal wird nur gesetzt, wenn beide Strategien übereinstimmen.
    Anschließend wird eine einfache Trade-Simulation durchgeführt.
    """
    df = df.copy()
    # Strategie A: 50-Tage-SMA
    df['SMA50'] = df['close'].rolling(window=50).mean()
    df['signal_A'] = 0
    df.loc[df['close'] > df['SMA50'], 'signal_A'] = 1
    df.loc[df['close'] < df['SMA50'], 'signal_A'] = -1

    # Strategie B: Bollinger Bands (20-Tage Standardabweichung)
    df['std20'] = df['close'].rolling(window=20).std()
    df['upper'] = df['SMA50'] + 2 * df['std20']
    df['lower'] = df['SMA50'] - 2 * df['std20']
    df['signal_B'] = 0
    df.loc[df['close'] < df['lower'], 'signal_B'] = 1
    df.loc[df['close'] > df['upper'], 'signal_B'] = -1

    # Aggregation: Nur wenn beide Signale übereinstimmen
    df['combined_signal'] = 0
    df.loc[(df['signal_A'] == 1) & (df['signal_B'] == 1), 'combined_signal'] = 1
    df.loc[(df['signal_A'] == -1) & (df['signal_B'] == -1), 'combined_signal'] = -1

    # Einfache Trade-Simulation
    kapital = start_kapital
    position = 0
    equity_curve = []
    for i in range(len(df)):
        preis = df.iloc[i]['close']
        signal = df.iloc[i]['combined_signal']
        if signal == 1 and position == 0:
            position = kapital / preis
            kapital = 0
        elif signal == -1 and position > 0:
            kapital = position * preis
            position = 0
        equity_curve.append(kapital + position * preis)
    final_value = equity_curve[-1]
    profit = final_value - start_kapital
    return final_value, profit

def main():
    # Hier holst Du zunächst alle verfügbaren Ticker (z.B. aus einer Liste oder DB)
    # Beispiel: Angenommen, get_available_stocks() gibt Dir eine Liste von Ticker zurück
    all_tickers = ["AAPL", "AMZN"]  # Beispiel
    tickers = filter_stocks(all_tickers)
    if not tickers:
        print("Keine Aktien verfügbar!")
        return
    # Für dieses Beispiel nehmen wir den ersten Ticker aus der gefilterten Liste
    ticker = tickers[0]
    start_date = "2010-01-01"
    end_date = "2020-12-31"
    df = load_stock_data(ticker, start_date, end_date)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)
        df.index = df.index.normalize()
    final_value, profit = run_strategy_signal_aggregation(df, start_kapital=100000)
    print(f"Signal Aggregation Strategy for {ticker}: Final Value = {final_value:.2f}, Profit = {profit:.2f}")

if __name__ == "__main__":
    main()

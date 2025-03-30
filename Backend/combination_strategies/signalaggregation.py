#!/usr/bin/env python
import sys
import os
import pandas as pd
import plotly.graph_objects as go

# Pfad erweitern, damit Module aus dem übergeordneten Verzeichnis gefunden werden
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from Datenbank.api import get_available_stocks, load_stock_data


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

    # Strategie B: Bollinger Bands mit 20-Tage-SMA
    df['SMA20'] = df['close'].rolling(window=20).mean()
    df['std20'] = df['close'].rolling(window=20).std()
    df['upper'] = df['SMA20'] + 2 * df['std20']
    df['lower'] = df['SMA20'] - 2 * df['std20']
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
    # Alle verfügbaren Ticker aus der DB laden
    all_tickers = get_available_stocks()
    tickers = filter_stocks(all_tickers)
    if not tickers:
        print("Keine Aktien verfügbar!")
        return

    start_date = "2018-01-01"
    end_date = "2023-12-31"
    
    # Ergebnisse sammeln und Listen für Durchschnittswerte initialisieren
    results = []
    final_values = []
    profits = []
    
    for ticker in tickers:
        df = load_stock_data(ticker, start_date, end_date)
        if df is None or df.empty:
            results.append(f"{ticker}: Keine Daten verfügbar!")
            continue
        # Sicherstellen, dass die benötigten Spalten vorhanden sind und der Index ein DatetimeIndex ist
        df = ensure_close_column(df)
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
            df.set_index("date", inplace=True)
            df.index = df.index.normalize()
        # Performance der kombinierten Signale berechnen
        final_value, profit = run_strategy_signal_aggregation(df, start_kapital=100000)
        result_line = f"Signal Aggregation Strategy for {ticker}: Final Value = {final_value:.2f}, Profit = {profit:.2f}"
        results.append(result_line)
        print(result_line)
        final_values.append(final_value)
        profits.append(profit)
    
    # Durchschnitt berechnen, falls Ergebnisse vorliegen
    if final_values and profits:
        avg_final_value = sum(final_values) / len(final_values)
        avg_profit = sum(profits) / len(profits)
        avg_line = f"Durchschnittlicher Endwert: {avg_final_value:.2f}, Durchschnittlicher Profit: {avg_profit:.2f}"
        results.append(avg_line)
        print(avg_line)
    
    # Header-Zeilen vorbereiten
    header_lines = []
    header_lines.append(f"Gehandelte Aktien: {', '.join(tickers)}")
    header_lines.append(f"Handelszeitraum: {start_date} bis {end_date}")
    if final_values and profits:
        avg_percent_gain = (avg_profit / 100000) * 100
        header_lines.append(f"Durchschnittlicher prozentualer Gewinn: {avg_percent_gain:.2f}%")
    
    # Ergebnisse in eine Textdatei schreiben (Header zuerst)
    with open("results_signal_aggregation.txt", "w") as f:
        f.write("\n".join(header_lines) + "\n\n")
        for line in results:
            f.write(line + "\n")

if __name__ == "__main__":
    main()

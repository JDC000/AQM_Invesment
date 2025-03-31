import sys
import os
import pandas as pd
import plotly.graph_objects as go

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from Datenbank.api import get_available_stocks, load_stock_data
from strategies.common import ensure_close_column, filter_stocks


def run_strategy_sma50_bollinger_bands(df, start_kapital=100000):
    df = df.copy()
    df['SMA50'] = df['close'].rolling(window=50).mean()
    df['signal_A'] = 0
    df.loc[df['close'] > df['SMA50'], 'signal_A'] = 1
    df.loc[df['close'] < df['SMA50'], 'signal_A'] = -1
    df['SMA20'] = df['close'].rolling(window=20).mean()
    df['std20'] = df['close'].rolling(window=20).std()
    df['upper'] = df['SMA20'] + 2 * df['std20']
    df['lower'] = df['SMA20'] - 2 * df['std20']
    df['signal_B'] = 0
    df.loc[df['close'] < df['lower'], 'signal_B'] = 1
    df.loc[df['close'] > df['upper'], 'signal_B'] = -1
    df['combined_signal'] = 0
    df.loc[(df['signal_A'] == 1) & (df['signal_B'] == 1), 'combined_signal'] = 1
    df.loc[(df['signal_A'] == -1) & (df['signal_B'] == -1), 'combined_signal'] = -1

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
    all_tickers = get_available_stocks()
    tickers = filter_stocks(all_tickers)
    if not tickers:
        print("Keine Aktien verfügbar!")
        return

    start_date = "2018-01-01"
    end_date = "2023-12-31"

    results = []
    final_values = []
    profits = []
    
    for ticker in tickers:
        df = load_stock_data(ticker, start_date, end_date)
        if df is None or df.empty:
            results.append(f"{ticker}: Keine Daten verfügbar!")
            continue
        df = ensure_close_column(df)
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
            df.set_index("date", inplace=True)
            df.index = df.index.normalize()
        final_value, profit = run_strategy_sma50_bollinger_bands(df, start_kapital=100000)
        result_line = f"Signal Aggregation Strategy for {ticker}: Final Value = {final_value:.2f}, Profit = {profit:.2f}"
        results.append(result_line)
        print(result_line)
        final_values.append(final_value)
        profits.append(profit)
    
    if final_values and profits:
        avg_final_value = sum(final_values) / len(final_values)
        avg_profit = sum(profits) / len(profits)
        avg_line = f"Durchschnittlicher Endwert: {avg_final_value:.2f}, Durchschnittlicher Profit: {avg_profit:.2f}"
        results.append(avg_line)
        print(avg_line)
    
    header_lines = []
    header_lines.append(f"Gehandelte Aktien: {', '.join(tickers)}")
    header_lines.append(f"Handelszeitraum: {start_date} bis {end_date}")
    if final_values and profits:
        avg_percent_gain = (avg_profit / 100000) * 100
        header_lines.append(f"Durchschnittlicher prozentualer Gewinn: {avg_percent_gain:.2f}%")
    
    with open("results_sma50_bollinger_bands.txt", "w") as f:
        f.write("\n".join(header_lines) + "\n\n")
        for line in results:
            f.write(line + "\n")

if __name__ == "__main__":
    main()

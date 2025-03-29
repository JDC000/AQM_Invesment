import os
import sys
import pandas as pd
import numpy as np

# Pfad erweitern, damit Module aus dem übergeordneten Verzeichnis gefunden werden
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from Datenbank.api import get_available_stocks, load_stock_data

def format_currency(value):
    return f"{value:,.2f}"

def save_results(final_value, profit, weights, start_kapital, strategy_combo=("Momentum", "Bollinger"), output_path="results_portfolio_optimization.txt"):
    """
    Speichert das Ergebnis der Portfolio-Optimierung in eine Textdatei.
    Existierende Dateien werden gelöscht bzw. überschrieben.
    """
    if os.path.exists(output_path):
        os.remove(output_path)
    
    avg_percent = profit / start_kapital * 100
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("Ergebnis der Portfolio-Optimierung:\n")
        f.write(f"Strategie-Kombination: {strategy_combo[0]} + {strategy_combo[1]}\n")
        f.write(f"Finaler Endwert: €{format_currency(final_value)}\n")
        f.write(f"Gewinn: €{format_currency(profit)} ({format_currency(avg_percent)} %)\n")
        f.write(f"Gewichte: {strategy_combo[0]} = {weights[0]:.3f}, {strategy_combo[1]} = {weights[1]:.3f}\n")
    
    print(f"Ergebnisse wurden in '{output_path}' gespeichert.")

# Dummy-Strategien, die Equity-Kurven zurückgeben
def strat_momentum(df, start_kapital):
    dates = df.index
    equity = pd.Series(start_kapital * (1 + 0.001 * np.arange(len(dates))), index=dates)
    return None, None, equity, equity.iloc[-1] - start_kapital

def strat_bollinger(df, start_kapital):
    dates = df.index
    equity = pd.Series(start_kapital * (1 + 0.002 * np.arange(len(dates))), index=dates)
    return None, None, equity, equity.iloc[-1] - start_kapital

def run_strategy_portfolio_optimization(df, start_kapital=100000):
    _, _, equity1, _ = strat_momentum(df, start_kapital=start_kapital)
    _, _, equity2, _ = strat_bollinger(df, start_kapital=start_kapital)
    ret1 = equity1.pct_change().dropna()
    ret2 = equity2.pct_change().dropna()
    returns = pd.concat([ret1, ret2], axis=1)
    returns.columns = ['Strategy1', 'Strategy2']
    cov_matrix = returns.cov()
    sigma1 = cov_matrix.loc['Strategy1', 'Strategy1']
    sigma2 = cov_matrix.loc['Strategy2', 'Strategy2']
    cov12 = cov_matrix.loc['Strategy1', 'Strategy2']
    denominator = sigma1 + sigma2 - 2 * cov12
    if denominator == 0:
        w1, w2 = 0.5, 0.5
    else:
        w1 = (sigma2 - cov12) / denominator
        w2 = 1 - w1
    combined_equity = w1 * equity1 + w2 * equity2
    final_value = combined_equity.iloc[-1]
    profit = final_value - start_kapital
    return final_value, profit, (w1, w2)

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

def main():
    # Alle verfügbaren Ticker aus der DB laden und filtern
    all_tickers = get_available_stocks()
    tickers = filter_stocks(all_tickers)
    if not tickers:
        print("Keine Aktien verfügbar!")
        return

    start_date = "2010-01-01"
    end_date = "2020-12-31"
    total_capital = 100000  # Gesamtstartkapital
    capital_per_stock = total_capital / len(tickers)

    aggregated_final_value = 0
    aggregated_profit = 0
    sum_w1 = 0
    sum_w2 = 0

    print("Ergebnisse der Portfolio-Optimierung für jede Aktie:")
    for ticker in tickers:
        # load_stock_data liefert ein DataFrame mit den Spalten 'date' und 'close'
        df = load_stock_data(ticker, start_date, end_date)
        # Setze die 'date'-Spalte als Index, falls noch nicht geschehen
        if 'date' in df.columns:
            df.set_index('date', inplace=True)
        final_value, profit, weights = run_strategy_portfolio_optimization(df, start_kapital=capital_per_stock)
        print(f"{ticker}: Final Value = {final_value:.2f}, Profit = {profit:.2f}, Weights = (Momentum: {weights[0]:.3f}, Bollinger: {weights[1]:.3f})")
        aggregated_final_value += final_value
        aggregated_profit += profit
        sum_w1 += weights[0]
        sum_w2 += weights[1]

    avg_w1 = sum_w1 / len(tickers)
    avg_w2 = sum_w2 / len(tickers)

    print("\nAggregierte Ergebnisse des gesamten Portfolios:")
    print(f"Gesamter Finalwert = {aggregated_final_value:.2f}, Gesamtgewinn = {aggregated_profit:.2f}")
    print(f"Durchschnittliche Gewichte: Momentum = {avg_w1:.3f}, Bollinger = {avg_w2:.3f}")

    # Speicherung der aggregierten Ergebnisse
    save_results(aggregated_final_value, aggregated_profit, (avg_w1, avg_w2), total_capital)

if __name__ == "__main__":
    main()

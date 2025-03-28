import pandas as pd
import numpy as np

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
    return final_value, profit

def load_stock_data(ticker, start_date, end_date):
    dates = pd.date_range(start_date, end_date)
    data = pd.DataFrame({"close": 100 + 0.1 * np.arange(len(dates))}, index=dates)
    return data

if __name__ == "__main__":
    ticker = "AAPL"
    start_date = "2010-01-01"
    end_date = "2020-12-31"
    df = load_stock_data(ticker, start_date, end_date)
    final_value, profit = run_strategy_portfolio_optimization(df, start_kapital=100000)
    print(f"Portfolio Optimization Strategy: Final Value = {final_value:.2f}, Profit = {profit:.2f}")

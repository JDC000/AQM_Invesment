import pandas as pd

# Dummy-Implementierungen für zwei Strategien
def strat_momentum(df, start_kapital):
    # Beispiel: 10% Gewinn
    return start_kapital * 1.1, start_kapital * 0.1

def strat_ma(df, start_kapital):
    # Beispiel: 20% Gewinn
    return start_kapital * 1.2, start_kapital * 0.2

def run_strategy_dynamic_weighting(df, start_kapital=100000):
    final1, profit1 = strat_momentum(df, start_kapital=start_kapital)
    final2, profit2 = strat_ma(df, start_kapital=start_kapital)
    ret1 = final1 / start_kapital
    ret2 = final2 / start_kapital
    if ret1 + ret2 == 0:
        w1, w2 = 0.5, 0.5
    else:
        w1 = ret1 / (ret1 + ret2)
        w2 = ret2 / (ret1 + ret2)
    combined_final = w1 * final1 + w2 * final2
    combined_profit = combined_final - start_kapital
    return combined_final, combined_profit

def load_stock_data(ticker, start_date, end_date):
    dates = pd.date_range(start_date, end_date)
    data = pd.DataFrame({"close": 100 + (pd.Series(range(len(dates))) * 0.1)}, index=dates)
    return data

if __name__ == "__main__":
    ticker = "AAPL"
    start_date = "2010-01-01"
    end_date = "2020-12-31"
    df = load_stock_data(ticker, start_date, end_date)
    final_value, profit = run_strategy_dynamic_weighting(df, start_kapital=100000)
    print(f"Dynamic Weighting Strategy: Final Value = {final_value:.2f}, Profit = {profit:.2f}")

import pandas as pd

def run_strategy_serial(df, start_kapital=100000):
    df = df.copy()
    df['SMA200'] = df['close'].rolling(window=200).mean()
    df['market_phase'] = 0
    df.loc[df['close'] >= df['SMA200'], 'market_phase'] = 1  # Bull Market
    df.loc[df['close'] < df['SMA200'], 'market_phase'] = -1  # Bear Market

    kapital = start_kapital
    position = 0
    equity_curve = []
    
    for i in range(len(df)):
        preis = df.iloc[i]['close']
        phase = df.iloc[i]['market_phase']
        if phase == 1:
            sma50 = df['close'].rolling(window=50).mean().iloc[i]
            signal = 1 if preis > sma50 else 0
        else:
            signal = 1  # Im Bear Market halten (Hold)
        if signal == 1 and position == 0:
            position = kapital / preis
            kapital = 0
        elif signal == 0 and position > 0:
            kapital = position * preis
            position = 0
        equity_curve.append(kapital + position * preis)
    
    final_value = equity_curve[-1]
    profit = final_value - start_kapital
    return final_value, profit

def load_stock_data(ticker, start_date, end_date):
    dates = pd.date_range(start_date, end_date)
    data = pd.DataFrame({"close": 100 + 0.1 * pd.Series(range(len(dates)))}, index=dates)
    return data

if __name__ == "__main__":
    ticker = "AAPL"
    start_date = "2010-01-01"
    end_date = "2020-12-31"
    df = load_stock_data(ticker, start_date, end_date)
    final_value, profit = run_strategy_serial(df, start_kapital=100000)
    print(f"Serial Application Strategy: Final Value = {final_value:.2f}, Profit = {profit:.2f}")

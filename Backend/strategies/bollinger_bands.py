import pandas as pd
import plotly.graph_objects as go

def run_strategy(df: pd.DataFrame, window: int = 20, num_std: int = 2, start_kapital: float = 100000):
    df = df.copy()
    df["MA"] = df["close"].rolling(window=window).mean()
    df["std"] = df["close"].rolling(window=window).std()
    df["upper_band"] = df["MA"] + num_std * df["std"]
    df["lower_band"] = df["MA"] - num_std * df["std"]

    df["signal"] = 0
    df.loc[df["close"] < df["lower_band"], "signal"] = 1
    df.loc[df["close"] > df["upper_band"], "signal"] = -1

    kapital = start_kapital
    position = 0
    equity_curve = []
    for i in range(len(df)):
        preis = df.iloc[i]["close"]
        signal = df.iloc[i]["signal"]
        if signal == 1 and position == 0:
            position = kapital / preis
            kapital = 0
        elif signal == -1 and position > 0:
            kapital = position * preis
            position = 0
        equity_curve.append(kapital + position * preis)

    final_value = equity_curve[-1] if equity_curve else start_kapital
    profit = final_value - start_kapital
    df["Equity"] = equity_curve

    x_values = df["date"] if "date" in df.columns else df.index

    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=x_values, y=df["close"], mode="lines", name="Schlusskurs"))
    fig1.add_trace(go.Scatter(x=x_values, y=df["MA"], mode="lines", name="MA"))
    fig1.add_trace(go.Scatter(x=x_values, y=df["upper_band"], mode="lines", name="Oberes Band",
                              line=dict(dash="dash", color="red")))
    fig1.add_trace(go.Scatter(x=x_values, y=df["lower_band"], mode="lines", name="Unteres Band",
                              line=dict(dash="dash", color="green")))
    
    kauf_signale = df[df["signal"] == 1]
    verkauf_signale = df[df["signal"] == -1]
    if "date" in df.columns:
        fig1.add_trace(go.Scatter(x=kauf_signale["date"], y=kauf_signale["close"], mode="markers",
                                  marker=dict(color="green", size=8), name="Kaufen"))
        fig1.add_trace(go.Scatter(x=verkauf_signale["date"], y=verkauf_signale["close"], mode="markers",
                                  marker=dict(color="red", size=8), name="Verkaufen"))
    else:
        fig1.add_trace(go.Scatter(x=kauf_signale.index, y=kauf_signale["close"], mode="markers",
                                  marker=dict(color="green", size=8), name="Kaufen"))
        fig1.add_trace(go.Scatter(x=verkauf_signale.index, y=verkauf_signale["close"], mode="markers",
                                  marker=dict(color="red", size=8), name="Verkaufen"))
    fig1.update_layout(title="Bollinger Bands Strategie", xaxis_title="Datum", yaxis_title="Preis", xaxis_type="date")

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=x_values, y=equity_curve, mode="lines", name="Equity"))
    fig2.update_layout(title="Kapitalentwicklung", xaxis_title="Datum", yaxis_title="Kapital", xaxis_type="date")

    return fig1, fig2, final_value, profit

def main():
    import sys, os, sqlite3, pandas as pd
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from strategies.common import ensure_close_column, ensure_datetime_index, format_currency
    

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    BASE_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
    DB_NAME = os.path.join(BASE_DIR, "Datenbank", "DB", "investment.db")
    
    symbol = "AAPL"
    start_date = "2010-01-01"
    end_date = "2020-12-31"
    
    try:
        conn = sqlite3.connect(DB_NAME)
        query = """
            SELECT date, close
            FROM market_data
            WHERE symbol = ? AND date BETWEEN ? AND ?
            ORDER BY date
        """
        params = [symbol, start_date, end_date]
        df_db = pd.read_sql_query(query, conn, params=params, parse_dates=["date"])
    except Exception as e:
        print("Fehler beim Laden der Daten aus der Datenbank:", e)
        sys.exit(1)
    finally:
        conn.close()
    
    try:
        df_db = ensure_close_column(df_db)
        df_db = ensure_datetime_index(df_db)
    except Exception as e:
        print("Fehler bei der Datenaufbereitung:", e)
        sys.exit(1)
    
    start_value = 100000
    fig1, fig2, final_value, profit = run_strategy(df_db, start_kapital=start_value)
    percent_change = (final_value - start_value) / start_value * 100

    print("Startwert: €" + format_currency(start_value))
    print("Endwert: €" + format_currency(final_value))
    print("Gewinn/Verlust: €" + format_currency(profit))
    print("Prozentuale Veränderung: " + format_currency(percent_change) + " %")
    #fig1.show()
    #fig2.show()

if __name__ == "__main__":
    main()

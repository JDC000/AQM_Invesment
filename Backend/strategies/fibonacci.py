import pandas as pd
import sqlite3
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from strategies.common import ensure_close_column, ensure_datetime_index, format_currency
import plotly.graph_objects as go

def run_strategy(df: pd.DataFrame, fenster: int = 50, tolerance: float = 0.01, start_kapital: float = 100000):
    df = df.copy()
    df["rolling_max"] = df["close"].rolling(window=fenster).max().shift(1)
    df["rolling_min"] = df["close"].rolling(window=fenster).min().shift(1)
    df["diff"] = df["rolling_max"] - df["rolling_min"]

    df["fib_38"] = df["rolling_max"] - 0.382 * df["diff"]
    df["fib_62"] = df["rolling_max"] - 0.618 * df["diff"]
    def get_signal(row):
        if pd.isna(row["fib_38"]) or pd.isna(row["fib_62"]):
            return 0
        if abs(row["close"] - row["fib_38"]) / row["fib_38"] < tolerance:
            return 1
        elif abs(row["close"] - row["fib_62"]) / row["fib_62"] < tolerance:
            return -1
        return 0
    df["signal"] = df.apply(get_signal, axis=1)
    kapital = start_kapital
    position = 0
    equity_curve = []
    buy_indices = []
    sell_indices = []
    
    for i in range(len(df)):
        preis = df.iloc[i]["close"]
        signal = df.iloc[i]["signal"]
        if signal == 1 and position == 0:
            position = kapital / preis
            kapital = 0
            buy_indices.append(i)
        elif signal == -1 and position > 0:
            kapital = position * preis
            position = 0
            sell_indices.append(i)
        equity_curve.append(kapital + position * preis)

    final_value = equity_curve[-1] if equity_curve else start_kapital
    gewinn = final_value - start_kapital

    x_values = df["date"] if "date" in df.columns else df.index
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=x_values, y=df["close"], mode="lines", name="Schlusskurs"))
    fig1.add_trace(go.Scatter(x=x_values, y=df["fib_38"], mode="lines", name="Fib 38.2%"))
    fig1.add_trace(go.Scatter(x=x_values, y=df["fib_62"], mode="lines", name="Fib 61.8%"))
    fig1.add_trace(go.Scatter(
        x=[x_values[i] for i in buy_indices],
        y=[df.iloc[i]["close"] for i in buy_indices],
        mode="markers", marker=dict(color="green", size=8), name="Kaufen"))
    fig1.add_trace(go.Scatter(
        x=[x_values[i] for i in sell_indices],
        y=[df.iloc[i]["close"] for i in sell_indices],
        mode="markers", marker=dict(color="red", size=8), name="Verkaufen"))
    fig1.update_layout(title="Fibonacci-Retracement Strategie", xaxis_title="Datum", yaxis_title="Preis", xaxis_type="date")

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=x_values, y=equity_curve, mode="lines", name="Equity"))
    fig2.update_layout(title="Kapitalentwicklung", xaxis_title="Datum", yaxis_title="Kapital", xaxis_type="date")

    return fig1, fig2, final_value, gewinn


if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    BASE_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
    DB_NAME = os.path.join(BASE_DIR, "Datenbank", "DB", "investment.db")

    symbol = "AVGO"
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
        print("Fehler beim Laden der Daten:", e)
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
    fig1, fig2, final_value, profit = run_strategy(df_db, fenster=50, tolerance=0.01, start_kapital=start_value)
    percent_change = (final_value - start_value) / start_value * 100

    print("Fibonacci-Retracement Strategie:")
    print("Startwert: €" + format_currency(start_value))
    print("Endwert: €" + format_currency(final_value))
    print("Gewinn/Verlust: €" + format_currency(profit))
    print("Prozentuale Veränderung: " + format_currency(percent_change) + " %")
    #fig1.show()
    #fig2.show()

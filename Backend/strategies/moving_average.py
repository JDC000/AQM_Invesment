import pandas as pd
import sqlite3
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from strategies.common import ensure_close_column, ensure_datetime_index, format_currency
import plotly.graph_objects as go

def run_strategy(df: pd.DataFrame, kurz_fenster: int = 50, lang_fenster: int = 200, start_kapital: float = 100000):
    df = df.copy()
    df["SMA_kurz"] = df["close"].rolling(window=kurz_fenster).mean()
    df["SMA_lang"] = df["close"].rolling(window=lang_fenster).mean()

    df["ma_diff"] = df["SMA_kurz"] - df["SMA_lang"]
    df["ma_diff_prev"] = df["ma_diff"].shift(1)

    df["signal"] = 0
    df.loc[(df["ma_diff"] > 0) & (df["ma_diff_prev"] <= 0), "signal"] = 1
    df.loc[(df["ma_diff"] < 0) & (df["ma_diff_prev"] >= 0), "signal"] = -1

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
        
    gesamtwert = kapital + position * df.iloc[-1]["close"]
    gewinn = gesamtwert - start_kapital
    df["Equity"] = equity_curve

    x_values = df["date"] if "date" in df.columns else df.index

    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=x_values, y=df["close"], mode="lines", name="Schlusskurs"))
    fig1.add_trace(go.Scatter(x=x_values, y=df["SMA_kurz"], mode="lines", name="SMA Kurz"))
    fig1.add_trace(go.Scatter(x=x_values, y=df["SMA_lang"], mode="lines", name="SMA Lang"))
    if "date" in df.columns:
        fig1.add_trace(go.Scatter(x=[x_values[i] for i in buy_indices],
                                  y=[df.iloc[i]["close"] for i in buy_indices],
                                  mode="markers", marker=dict(color="green", size=8), name="Kaufen"))
        fig1.add_trace(go.Scatter(x=[x_values[i] for i in sell_indices],
                                  y=[df.iloc[i]["close"] for i in sell_indices],
                                  mode="markers", marker=dict(color="red", size=8), name="Verkaufen"))
    else:
        fig1.add_trace(go.Scatter(x=[df.index[i] for i in buy_indices],
                                  y=[df.iloc[i]["close"] for i in buy_indices],
                                  mode="markers", marker=dict(color="green", size=8), name="Kaufen"))
        fig1.add_trace(go.Scatter(x=[df.index[i] for i in sell_indices],
                                  y=[df.iloc[i]["close"] for i in sell_indices],
                                  mode="markers", marker=dict(color="red", size=8), name="Verkaufen"))
    fig1.update_layout(title="MA Crossover Strategie", xaxis_title="Datum", yaxis_title="Preis", xaxis_type="date")

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=x_values, y=equity_curve, mode="lines", name="Equity"))
    fig2.update_layout(title="Kapitalentwicklung", xaxis_title="Datum", yaxis_title="Kapital", xaxis_type="date")

    return fig1, fig2, gesamtwert, gewinn


if __name__ == "__main__":
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
        print("Fehler beim Laden der Daten:", e)
        import sys; sys.exit(1)
    finally:
        conn.close()

    try:
        from common import ensure_close_column, ensure_datetime_index, format_currency
        df_db = ensure_close_column(df_db)
        df_db = ensure_datetime_index(df_db)
    except Exception as e:
        print("Fehler bei der Datenaufbereitung:", e)
        import sys; sys.exit(1)

    start_value = 100000
    fig1, fig2, gesamtwert, profit = run_strategy(df_db, kurz_fenster=50, lang_fenster=200, start_kapital=start_value)
    percent_change = (gesamtwert - start_value) / start_value * 100

    print("MA Crossover Strategie:")
    print("Startwert: €" + format_currency(start_value))
    print("Endwert: €" + format_currency(gesamtwert))
    print("Gewinn/Verlust: €" + format_currency(profit))
    print("Prozentuale Veränderung: " + format_currency(percent_change) + " %")
    #fig1.show()
    #fig2.show()

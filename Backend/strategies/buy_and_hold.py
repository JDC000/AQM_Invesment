import pandas as pd
import sqlite3
import os
import sys
from .common import ensure_close_column, ensure_datetime_index, format_currency
import plotly.graph_objects as go

def run_strategy(df: pd.DataFrame, start_kapital: float = 100000):
    """
    Buy and Hold Strategie:
    - Investiert am frühestmöglichen Tag das gesamte Kapital und verkauft am spätesten
    - Simuliert Trades (alles rein, alles raus) und berechnet die Equity-Kurve
    - Gibt 2 Plotly-Figuren + gesamtwert + gewinn zurück
    """
    df = df.copy()
    df["signal"] = 0
    if not df.empty:
        # Falls 'date'-Spalte vorhanden, verwende diese; ansonsten den Index
        if "date" in df.columns:
            df.iloc[0, df.columns.get_loc("signal")] = 1   # Kauf am ersten Tag
            df.iloc[-1, df.columns.get_loc("signal")] = -1   # Verkauf am letzten Tag
        else:
            df.iloc[0, df.columns.get_loc("signal")] = 1
            df.iloc[-1, df.columns.get_loc("signal")] = -1

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
    
    gesamtwert = equity_curve[-1] if equity_curve else start_kapital
    gewinn = gesamtwert - start_kapital
    df["Equity"] = equity_curve

    x_values = df["date"] if "date" in df.columns else df.index

    # Graph 1: Kurschart mit Kauf-/Verkaufspunkten
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=x_values, y=df["close"], mode="lines", name="Schlusskurs"))
    buy_signale = df[df["signal"] == 1]
    sell_signale = df[df["signal"] == -1]
    if "date" in df.columns:
        fig1.add_trace(go.Scatter(x=buy_signale["date"], y=buy_signale["close"], mode="markers",
                                  marker=dict(color="green", size=8), name="Kaufen"))
        fig1.add_trace(go.Scatter(x=sell_signale["date"], y=sell_signale["close"], mode="markers",
                                  marker=dict(color="red", size=8), name="Verkaufen"))
    else:
        fig1.add_trace(go.Scatter(x=buy_signale.index, y=buy_signale["close"], mode="markers",
                                  marker=dict(color="green", size=8), name="Kaufen"))
        fig1.add_trace(go.Scatter(x=sell_signale.index, y=sell_signale["close"], mode="markers",
                                  marker=dict(color="red", size=8), name="Verkaufen"))
    fig1.update_layout(title="Buy and Hold Strategie", xaxis_title="Datum", yaxis_title="Preis", xaxis_type="date")

    # Graph 2: Equity-Kurve
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
    fig1, fig2, gesamtwert, gewinn = run_strategy(df_db, start_kapital=start_value)
    percent_change = (gesamtwert - start_value) / start_value * 100

    from common import format_currency
    print("Buy and Hold Strategie:")
    print("Startwert: €" + format_currency(start_value))
    print("Endwert: €" + format_currency(gesamtwert))
    print("Gewinn/Verlust: €" + format_currency(gewinn))
    print("Prozentuale Veränderung: " + format_currency(percent_change) + " %")
    fig1.show()
    fig2.show()

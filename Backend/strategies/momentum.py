import pandas as pd
import sqlite3
import os
import sys
from .common import ensure_close_column, ensure_datetime_index, format_currency
import plotly.graph_objects as go

def run_strategy(df: pd.DataFrame, window: int = 20, start_kapital: float = 100000):
    """
    Momentum-Strategie:
    - Berechnet das Momentum als relative Kursänderung über ein Fenster
    - Generiert ein Kaufsignal, wenn das Momentum positiv und steigend ist,
      ansonsten wird verkauft.
    - Simuliert Trades (alles rein, alles raus), baut eine Equity-Kurve auf
    - Gibt 2 Plotly-Figuren + final_value + gewinn zurück
    """
    df = df.copy()
    df['Momentum'] = df['close'] / df['close'].shift(window) - 1
    df['Signal'] = ((df['Momentum'] > 0) & (df['Momentum'] > df['Momentum'].shift(1))).astype(int)
    
    kapital = start_kapital
    position = 0
    equity_curve = []
    buy_indices = []
    sell_indices = []
    
    for i in range(len(df)):
        preis = df.iloc[i]['close']
        signal = df.iloc[i]['Signal']
        # Bei Signal==1 und keiner Position: kaufen
        if signal == 1 and position == 0:
            position = kapital / preis
            kapital = 0
            buy_indices.append(i)
        # Wenn Signal nicht 1 (also 0) und Position vorhanden: verkaufen
        elif signal == 0 and position > 0:
            kapital = position * preis
            position = 0
            sell_indices.append(i)
        equity_curve.append(kapital + position * preis)
    
    final_value = equity_curve[-1] if equity_curve else start_kapital
    gewinn = final_value - start_kapital
    df["Equity"] = equity_curve

    x_values = df["date"] if "date" in df.columns else df.index

    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=x_values, y=df["close"], mode="lines", name="Schlusskurs"))
    # Marker für Kauf- und Verkaufspunkte
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
    fig1.update_layout(title="Momentum Strategie", xaxis_title="Datum", yaxis_title="Preis", xaxis_type="date")

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=x_values, y=equity_curve, mode="lines", name="Equity"))
    fig2.update_layout(title="Kapitalentwicklung", xaxis_title="Datum", yaxis_title="Kapital", xaxis_type="date")

    return fig1, fig2, final_value, gewinn

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
    fig1, fig2, final_value, profit = run_strategy(df_db, window=20, start_kapital=start_value)
    percent_change = (final_value - start_value) / start_value * 100

    print("Momentum Strategie:")
    from common import format_currency
    print("Startwert: €" + format_currency(start_value))
    print("Endwert: €" + format_currency(final_value))
    print("Gewinn/Verlust: €" + format_currency(profit))
    print("Prozentuale Veränderung: " + format_currency(percent_change) + " %")
    fig1.show()
    fig2.show()

import sqlite3
import pandas as pd
import os
import plotly.graph_objects as go

def run_strategy(df: pd.DataFrame, fenster: int = 20, start_kapital: float = 100000):
    """
    Breakout-Strategie:
    - Kauft, wenn der Schlusskurs das bisherige Hoch (letzte 'fenster' Tage, um 1 Tag verschoben) überschreitet
    - Verkauft, wenn der Schlusskurs das bisherige Tief unterschreitet
    - Simuliert Trades (alles rein, alles raus) und berechnet die Equity-Kurve
    - Gibt 2 Plotly-Figuren + final_value + gewinn zurück
    """
    df = df.copy()
    
    # Berechne Highest und Lowest der letzten 'fenster' Tage (um 1 Tag verschoben)
    df["highest"] = df["close"].rolling(window=fenster).max().shift(1)
    df["lowest"] = df["close"].rolling(window=fenster).min().shift(1)
    
    # Generiere Signale: 1 = Kaufsignal, -1 = Verkaufssignal
    df["signal"] = 0
    df.loc[df["close"] > df["highest"], "signal"] = 1
    df.loc[df["close"] < df["lowest"], "signal"] = -1
    
    # Trade-Simulation
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
    gewinn = final_value - start_kapital
    df["Equity"] = equity_curve

    x_values = df["date"] if "date" in df.columns else df.index

    # Graph 1: Kurschart mit Highest/Lowest und Signalen
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=x_values, y=df["close"], mode="lines", name="Schlusskurs"))
    fig1.add_trace(go.Scatter(x=x_values, y=df["highest"], mode="lines", name="Highest (verschoben)",
                              line=dict(dash="dash", color="red")))
    fig1.add_trace(go.Scatter(x=x_values, y=df["lowest"], mode="lines", name="Lowest (verschoben)",
                              line=dict(dash="dash", color="green")))
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
    fig1.update_layout(title="Breakout Strategie", xaxis_title="Datum", yaxis_title="Preis", xaxis_type="date")

    # Graph 2: Equity-Kurve
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=x_values, y=equity_curve, mode="lines", name="Equity"))
    fig2.update_layout(title="Kapitalentwicklung", xaxis_title="Datum", yaxis_title="Kapital", xaxis_type="date")
    
    return fig1, fig2, final_value, gewinn

# -------------------------
# Test-Main in der Strategie
# -------------------------
if __name__ == "__main__":
    import sys
    from common import ensure_close_column, ensure_datetime_index, format_currency
    import sqlite3
    import pandas as pd
    import os

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    BASE_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
    DB_NAME = os.path.join(BASE_DIR, "Datenbank", "DB", "investment.db")

    symbol = "AAPL"
    start_date = "2010-01-01"
    end_date = "2023-12-31"

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
    fig1, fig2, final_value, gewinn = run_strategy(df_db, fenster=20, start_kapital=start_value)
    percent_change = (final_value - start_value) / start_value * 100

    print("Startwert: €" + format_currency(start_value))
    print("Endwert: €" + format_currency(final_value))
    print("Gewinn/Verlust: €" + format_currency(gewinn))
    print("Prozentuale Veränderung: " + format_currency(percent_change) + " %")
    fig1.show()
    fig2.show()

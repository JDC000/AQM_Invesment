import pandas as pd
import sqlite3
import os
import sys
from .common import ensure_close_column, ensure_datetime_index, format_currency
import plotly.graph_objects as go

def run_strategy(df: pd.DataFrame, start_kapital: float = 100000):
    """
    Buy-September / Sell-December Strategie:
    - Setzt am ersten Handelstag im September ein Kaufsignal und
      am ersten Handelstag im Dezember ein Verkaufssignal.
    - Simuliert Trades (alles rein, alles raus) und baut eine Equity-Kurve auf
    - Gibt 2 Plotly-Figuren + gesamtwert + gewinn zurück
    """
    df = df.copy()
    # Falls vorhanden, setze die "date"-Spalte als Index
    if "date" in df.columns:
        df.set_index("date", inplace=True)
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
    df.index = df.index.normalize()

    df["signal"] = 0
    grouped = df.groupby([df.index.year, df.index.month])
    for (year, month), group in grouped:
        first_day = group.index.min()
        if month == 9:
            df.loc[first_day, "signal"] = 1
        elif month == 12:
            df.loc[first_day, "signal"] = -1

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

    x_values = df.index

    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=x_values, y=df["close"], mode="lines", name="Schlusskurs"))
    # Markiere Kauf- und Verkaufssignale
    kauf_signale = df[df["signal"] == 1]
    verkauf_signale = df[df["signal"] == -1]
    fig1.add_trace(go.Scatter(x=kauf_signale.index, y=kauf_signale["close"], mode="markers",
                              marker=dict(color="green", size=8), name="Kaufen"))
    fig1.add_trace(go.Scatter(x=verkauf_signale.index, y=verkauf_signale["close"], mode="markers",
                              marker=dict(color="red", size=8), name="Verkaufen"))
    fig1.update_layout(title="Buy-September / Sell-December Strategie", xaxis_title="Datum", yaxis_title="Preis", xaxis_type="date")

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=x_values, y=equity_curve, mode="lines", name="Equity"))
    fig2.update_layout(title="Kapitalentwicklung", xaxis_title="Datum", yaxis_title="Kapital", xaxis_type="date")

    return fig1, fig2, gesamtwert, gewinn

# -------------------------
# Test-Main Buy-September / Sell-December
# -------------------------
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
    fig1, fig2, gesamtwert, profit = run_strategy(df_db, start_kapital=start_value)
    percent_change = (gesamtwert - start_value) / start_value * 100

    print("Buy-September / Sell-December Strategie:")
    from common import format_currency
    print("Startwert: €" + format_currency(start_value))
    print("Endwert: €" + format_currency(gesamtwert))
    print("Gewinn/Verlust: €" + format_currency(profit))
    print("Prozentuale Veränderung: " + format_currency(percent_change) + " %")
    fig1.show()
    fig2.show()

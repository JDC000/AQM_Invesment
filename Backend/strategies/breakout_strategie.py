import sqlite3
import pandas as pd
import plotly.graph_objects as go
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "DB", "investment.db")

def run_strategy(df: pd.DataFrame, fenster=20, start_kapital=100000):
    """
    Breakout-Strategie:
    - Kauft, wenn der Schlusskurs das bisherige Hoch (letzte 'fenster' Tage) überschreitet
    - Verkauft, wenn der Schlusskurs das bisherige Tief unterschreitet
    - Einfache Trade-Simulation
    """
    df = df.copy()

    # --- 1) Signale ---
    df["highest"] = df["close"].rolling(window=fenster).max().shift(1)
    df["lowest"] = df["close"].rolling(window=fenster).min().shift(1)
    df["signal"] = 0
    df.loc[df["close"] > df["highest"], "signal"] = 1
    df.loc[df["close"] < df["lowest"], "signal"] = -1

    # --- 2) Einfache Trade-Simulation ---
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

    df["Equity"] = equity_curve
    final_value = equity_curve[-1] if equity_curve else start_kapital
    gewinn = final_value - start_kapital

    # --- 3) Plotly-Figuren ---
    # fig1: Schlusskurs + Highest/Lowest + Signale
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=df['date'], y=df["close"], mode="lines", name="Schlusskurs"))
    fig1.add_trace(go.Scatter(x=df['date'], y=df["highest"], mode="lines",
                              name="Höchster Kurs (Vorperiode)", line=dict(dash="dash", color="orange")))
    fig1.add_trace(go.Scatter(x=df['date'], y=df["lowest"], mode="lines",
                              name="Tiefster Kurs (Vorperiode)", line=dict(dash="dash", color="blue")))

    kauf_signale = df[df["signal"] == 1]
    verkauf_signale = df[df["signal"] == -1]
    fig1.add_trace(go.Scatter(x=kauf_signale.index, y=kauf_signale["close"], mode="markers",
                              marker=dict(color="green", size=8), name="Kaufen"))
    fig1.add_trace(go.Scatter(x=verkauf_signale.index, y=verkauf_signale["close"], mode="markers",
                              marker=dict(color="red", size=8), name="Verkaufen"))

    fig1.update_layout(title="Breakout-Strategie – Kursverlauf", xaxis_title="Datum", yaxis_title="Preis")

    # fig2: Kapitalentwicklung
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=df['date'], y=df["Equity"], mode="lines", name="Equity"))
    fig2.update_layout(title="Breakout-Strategie – Kapitalentwicklung", 
                      xaxis_title="Datum", yaxis_title="Kapital")

    return fig1, fig2, final_value, gewinn


# --- Optionaler Testlauf ---
if __name__ == "__main__":
    def lade_daten(symbol, start_datum="2010-01-01", end_datum="2020-12-31"):
        conn = sqlite3.connect(DB_NAME)
        query = f"""
            SELECT date, close FROM market_data 
            WHERE symbol = '{symbol}' 
            AND date BETWEEN '{start_datum}' AND '{end_datum}'
        """
        df_local = pd.read_sql_query(query, conn)
        conn.close()
        df_local["date"] = pd.to_datetime(df_local["date"])
        df_local.set_index("date", inplace=True)
        return df_local

    symbol = "AAPL"
    df_test = lade_daten(symbol)
    figA, figB, end_value, profit = run_strategy(df_test)
    figA.show()
    figB.show()
    print("Endwert:", end_value, "Gewinn:", profit)

import sqlite3
import pandas as pd
import plotly.graph_objects as go
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "DB", "investment.db")

def run_strategy(df: pd.DataFrame, fenster=50, tolerance=0.01, start_kapital=100000):
    """
    Fibonacci-Retracement-Strategie mit einfacher Trade-Simulation.
    
    - 'fenster': Anzahl Tage für rollierendes Hoch/Tief
    - 'tolerance': Prozentuale Abweichung, um ein Level als 'nahe' zu betrachten
    - 'start_kapital': Startkapital in €
    """
    df = df.copy()

    # --- 1) Fibonacci-Level berechnen ---
    df["rolling_max"] = df["close"].rolling(window=fenster).max().shift(1)
    df["rolling_min"] = df["close"].rolling(window=fenster).min().shift(1)
    df["diff"] = df["rolling_max"] - df["rolling_min"]

    df["fib_0"]   = df["rolling_max"]
    df["fib_23"]  = df["rolling_max"] - 0.236 * df["diff"]
    df["fib_38"]  = df["rolling_max"] - 0.382 * df["diff"]
    df["fib_50"]  = df["rolling_max"] - 0.5   * df["diff"]
    df["fib_62"]  = df["rolling_max"] - 0.618 * df["diff"]
    df["fib_100"] = df["rolling_min"]

    # --- 2) Kauf-/Verkaufssignale generieren ---
    def get_signal(row):
        if pd.isna(row["fib_38"]) or pd.isna(row["fib_62"]):
            return 0
        # Kaufsignal, wenn Kurs nahe am 38,2%-Level
        if abs(row["close"] - row["fib_38"]) / row["fib_38"] < tolerance:
            return 1
        # Verkaufssignal, wenn Kurs nahe am 61,8%-Level
        elif abs(row["close"] - row["fib_62"]) / row["fib_62"] < tolerance:
            return -1
        return 0

    df["signal"] = df.apply(get_signal, axis=1)

    # --- 3) Einfache Trade-Simulation ---
    kapital = start_kapital
    position = 0
    equity_curve = []

    for i in range(len(df)):
        preis = df.iloc[i]["close"]
        signal = df.iloc[i]["signal"]

        if signal == 1 and position == 0:
            # Kaufen (alles rein)
            position = kapital / preis
            kapital = 0
        elif signal == -1 and position > 0:
            # Verkaufen (alles raus)
            kapital = position * preis
            position = 0

        equity_curve.append(kapital + position * preis)

    df["Equity"] = equity_curve
    final_value = equity_curve[-1] if equity_curve else start_kapital
    gewinn = final_value - start_kapital

    # --- 4) Plotly-Figuren ---
    # fig1: Schlusskurs + Fib-Linien + Kauf/Verkauf
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=df.index, y=df["close"], mode="lines", name="Schlusskurs"))
    fig1.add_trace(go.Scatter(x=df.index, y=df["fib_38"], mode="lines", name="Fib 38,2%", line=dict(dash="dash", color="green")))
    fig1.add_trace(go.Scatter(x=df.index, y=df["fib_62"], mode="lines", name="Fib 61,8%", line=dict(dash="dash", color="red")))

    kauf_signale = df[df["signal"] == 1]
    verkauf_signale = df[df["signal"] == -1]
    fig1.add_trace(go.Scatter(x=kauf_signale.index, y=kauf_signale["close"], mode="markers", 
                              marker=dict(color="green", size=8), name="Kaufen"))
    fig1.add_trace(go.Scatter(x=verkauf_signale.index, y=verkauf_signale["close"], mode="markers", 
                              marker=dict(color="red", size=8), name="Verkaufen"))
    fig1.update_layout(title="Fibonacci Strategie", xaxis_title="Datum", yaxis_title="Preis")

    # fig2: Kapitalentwicklung
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=df.index, y=df["Equity"], mode="lines", name="Equity-Kurve"))
    fig2.update_layout(title="Fibonacci Strategie – Kapitalentwicklung", 
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

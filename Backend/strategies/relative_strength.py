import sqlite3
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "DB", "investment.db")

def run_strategy(df: pd.DataFrame, fenster=14, overkauft=70, oversold=30, start_kapital=100000):
    """
    RSI-Strategie mit einfacher Trade-Simulation.
    
    - 'fenster': Anzahl Tage für die RSI-Berechnung
    - 'overkauft': RSI-Schwelle für Verkaufssignal
    - 'oversold': RSI-Schwelle für Kaufsignal
    - 'start_kapital': Startkapital in €
    """
    df = df.copy()

    # --- 1) RSI berechnen ---
    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(window=fenster, min_periods=fenster).mean()
    avg_loss = loss.rolling(window=fenster, min_periods=fenster).mean()

    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))

    # --- 2) Signale ---
    df["signal"] = 0
    df.loc[df["RSI"] < oversold, "signal"] = 1    # Kaufen
    df.loc[df["RSI"] > overkauft, "signal"] = -1  # Verkaufen

    # --- 3) Einfache Trade-Simulation ---
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

    # --- 4) Plotly-Figuren ---
    # fig1: Schlusskurs + Kauf/Verkauf
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=df.index, y=df["close"], mode="lines", name="Schlusskurs"))
    kauf_signale = df[df["signal"] == 1]
    verkauf_signale = df[df["signal"] == -1]
    fig1.add_trace(go.Scatter(x=kauf_signale.index, y=kauf_signale["close"], mode="markers",
                              marker=dict(color="green", size=8), name="Kaufen"))
    fig1.add_trace(go.Scatter(x=verkauf_signale.index, y=verkauf_signale["close"], mode="markers",
                              marker=dict(color="red", size=8), name="Verkaufen"))
    fig1.update_layout(title="RSI Strategie – Kursverlauf", xaxis_title="Datum", yaxis_title="Preis")

    # fig2: Subplots für Equity-Kurve (oben) und RSI (unten)
    fig2 = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05,
                         subplot_titles=("Kapitalentwicklung", "RSI"))
    # -- Equity-Kurve
    fig2.add_trace(go.Scatter(x=df.index, y=df["Equity"], mode="lines", name="Equity"), row=1, col=1)
    # -- RSI
    fig2.add_trace(go.Scatter(x=df.index, y=df["RSI"], mode="lines", name="RSI"), row=2, col=1)
    # Overbought/Oversold-Linien
    fig2.add_hline(y=overkauft, line_dash="dash", line_color="red", row=2, col=1)
    fig2.add_hline(y=oversold, line_dash="dash", line_color="green", row=2, col=1)

    fig2.update_layout(title="RSI Strategie – Equity & RSI")

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

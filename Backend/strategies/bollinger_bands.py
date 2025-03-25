import sqlite3
import pandas as pd
import plotly.graph_objects as go
import os
import numpy as np

def run_strategy(
    df: pd.DataFrame, 
    window: int = 20, 
    num_std: int = 2, 
    start_kapital: float = 100000
):
    """
    Bollinger-Bands-Strategie:
    - Signalgenerierung (signal = 1 bei Unterschreiten des unteren Bandes, -1 bei Überschreiten des oberen Bandes)
    - Einfache Trade-Simulation (alles rein, alles raus)
    - Gibt 2 Plotly-Figuren + final_value + Gewinn zurück
    """
    # 1) Bollinger-Bands berechnen
    df = df.copy()
    df["MA"] = df["close"].rolling(window=window).mean()
    df["std"] = df["close"].rolling(window=window).std()
    df["upper_band"] = df["MA"] + num_std * df["std"]
    df["lower_band"] = df["MA"] - num_std * df["std"]

    # Signale: Kaufen = 1, Verkaufen = -1
    df["signal"] = 0
    df.loc[df["close"] < df["lower_band"], "signal"] = 1    # Kaufsignal
    df.loc[df["close"] > df["upper_band"], "signal"] = -1   # Verkaufssignal

    # 2) Einfache Trade-Simulation
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

    # 3) Plotly-Figuren erstellen
    # fig1: Kurs + Bollinger Bands + Kauf-/Verkaufspunkte
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=df["date"], y=df["close"], mode="lines", name="Schlusskurs"))
    fig1.add_trace(go.Scatter(x=df["date"], y=df["MA"], mode="lines", name="MA"))
    fig1.add_trace(go.Scatter(x=df["date"], y=df["upper_band"], mode="lines", name="Oberes Band",
                              line=dict(dash="dash", color="red")))
    fig1.add_trace(go.Scatter(x=df["date"], y=df["lower_band"], mode="lines", name="Unteres Band",
                              line=dict(dash="dash", color="green")))
    
    kauf_signale = df[df["signal"] == 1]
    verkauf_signale = df[df["signal"] == -1]
    # Hier wird explizit die "date"-Spalte genutzt:
    fig1.add_trace(go.Scatter(x=kauf_signale["date"], y=kauf_signale["close"], mode="markers",
                              marker=dict(color="green", size=8), name="Kaufen"))
    fig1.add_trace(go.Scatter(x=verkauf_signale["date"], y=verkauf_signale["close"], mode="markers",
                              marker=dict(color="red", size=8), name="Verkaufen"))
    
    fig1.update_layout(
        title="Bollinger Bands Strategie",
        xaxis_title="Datum",
        yaxis_title="Preis",
        xaxis_type='date'
    )

    # fig2: Equity-Kurve
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=df["date"], y=df["Equity"], mode="lines", name="Equity"))
    fig2.update_layout(
        title="Kapitalentwicklung",
        xaxis_title="Datum",
        yaxis_title="Kapital",
        xaxis_type='date'
    )

    return fig1, fig2, final_value, gewinn

# -------------------------
# Testlauf – Beispiel-Daten erstellen
# -------------------------
if __name__ == "__main__":
    # Beispielhafte Kursdaten generieren
    dates = pd.date_range(start="2020-01-01", periods=100, freq="D")
    np.random.seed(0)
    # Simulierter Kursverlauf: Zufallszahlen, kumulativ aufsummiert
    close = np.cumsum(np.random.randn(100)) + 100  
    df_test = pd.DataFrame({"date": dates, "close": close})
    
    # Strategie ausführen
    fig1, fig2, final_value, profit = run_strategy(df_test)
    fig1.show()
    fig2.show()
    print("Final Value:", final_value, "Profit:", profit)

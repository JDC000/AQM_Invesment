import pandas as pd
import plotly.graph_objects as go

def run_strategy(df: pd.DataFrame, start_kapital=100000):
    """
    Buy and Hold Strategie:
    - Zum frühestmöglichen Zeitpunkt wird das gesamte Kapital investiert.
    - Zum spätestmöglichen Zeitpunkt wird die Position verkauft.
    
    Parameter:
        df (pd.DataFrame): DataFrame mit historischen Preisdaten. 
                           Erwartete Spalten: "date" (Datum) und "close" (Schlusskurs).
        start_kapital (float): Das initiale Startkapital.
    
    Rückgabe:
        tuple: (fig1, fig2, gesamtwert, gewinn)
               fig1: Diagramm mit Kursentwicklung und Kauf-/Verkaufspunkten.
               fig2: Diagramm mit Gesamtvermögen nach den Transaktionen.
               gesamtwert: Endwert der Strategie.
               gewinn: Gewinn (oder Verlust) gegenüber dem Startkapital.
    """
    df = df.copy()

    # Signale initialisieren: 0 = keine Aktion
    df["signal"] = 0
    if not df.empty:
        df.loc[df.index[0], "signal"] = 1   # Kauf am frühestmöglichen Zeitpunkt
        df.loc[df.index[-1], "signal"] = -1   # Verkauf am spätestmöglichen Zeitpunkt

    # === Simulation von Transaktionen ===
    kapital = start_kapital
    position = 0
    eigenkapital_punkte = []

    for i in range(len(df)):
        zeile = df.iloc[i]
        datum = zeile["date"]
        preis = zeile["close"]
        signal = zeile["signal"]

        if signal == 1 and position == 0:
            position = kapital / preis
            kapital = 0
            eigenkapital_punkte.append((datum, position * preis))
        elif signal == -1 and position > 0:
            kapital = position * preis
            position = 0
            eigenkapital_punkte.append((datum, kapital))

    # Gesamtwert am Ende
    if position > 0:
        gesamtwert = kapital + position * df.iloc[-1]["close"]
    else:
        gesamtwert = kapital

    gewinn = gesamtwert - start_kapital

    # === Diagramm 1: Kursentwicklung und Kauf-/Verkaufspunkte ===
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=df["date"], y=df["close"], name="Aktienkurs", line=dict(color="gray")))
    
    kaufen = df[df["signal"] == 1]
    verkaufen = df[df["signal"] == -1]

    fig1.add_trace(go.Scatter(
        x=kaufen["date"], y=kaufen["close"], mode="markers", name="Kaufen",
        marker=dict(color="green", symbol="triangle-up", size=10)
    ))

    fig1.add_trace(go.Scatter(
        x=verkaufen["date"], y=verkaufen["close"], mode="markers", name="Verkaufen",
        marker=dict(color="red", symbol="triangle-down", size=10)
    ))

    fig1.update_layout(
        title="Buy and Hold Strategie – Kauf/Verkauf Signale",
        xaxis_title="Datum", yaxis_title="Aktienkurs (€)"
    )
    
    # === Diagramm 2: Gesamtvermögen nach den Transaktionen ===
    fig2 = go.Figure()
    if eigenkapital_punkte:
        daten, werte = zip(*eigenkapital_punkte)
        fig2.add_trace(go.Scatter(
            x=daten, y=werte,
            mode="lines+markers",
            name="Gesamtvermögen",
            marker=dict(color="green", size=8),
            line=dict(color="green", width=2)
        ))

    fig2.update_layout(
        title="Gesamtvermögen nach jeder Transaktion",
        xaxis_title="Datum", yaxis_title="Vermögen (€)"
    )

    return fig1, fig2, gesamtwert, gewinn

import pandas as pd
import plotly.graph_objects as go

def run_strategy(data: pd.DataFrame, window: int = 20, start_kapital: float = 100000):
    df = data.copy()
    df['Momentum'] = df['close'] / df['close'].shift(window) - 1
    df['Signal'] = (df['Momentum'] > 0) & (df['Momentum'] > df['Momentum'].shift(1))
    df['Signal'] = df['Signal'].astype(int)

    # Berechnung des Kapitals
    position = 0
    kapital = start_kapital
    eigenkapital = []

    for i in range(len(df)):
        preis = df.loc[i, 'close']
        signal = df.loc[i, 'Signal']

        if signal == 1 and position == 0:
            position = kapital / preis
            kapital = 0
        elif signal == 0 and position > 0:
            kapital = position * preis
            position = 0

        gesamtwert = kapital + position * preis
        eigenkapital.append(gesamtwert)

    df['Equity'] = eigenkapital
    final_value = eigenkapital[-1] if eigenkapital else start_kapital
    gewinn = final_value - start_kapital

    # --- Diagramm 1: Momentum-Signale ---
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=df['date'], y=df['close'], name="Schlusskurs"))
    fig1.add_trace(go.Scatter(x=df['date'], y=df['Momentum'] * df['close'],
                              name="Momentum x Preis", line=dict(dash='dot')))
    fig1.update_layout(title="Momentum Signale", xaxis_title="Datum", yaxis_title="Preis")

    # --- Diagramm 2: Equity-Kurve ---
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=df['date'], y=df['Equity'], name="Equity-Kurve"))
    fig2.update_layout(title="Kapitalentwicklung", xaxis_title="Datum", yaxis_title="Kapital (€)")

    return fig1, fig2, final_value, gewinn

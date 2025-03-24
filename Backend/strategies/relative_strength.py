import sqlite3
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

DB_NAME = "/Users/hendrik_liebscher/Desktop/Git/AQM_Invesment/Backend/Datenbank/DB/investment.db"

def lade_daten(symbol, start_datum="2010-01-01", end_datum="2020-12-31"):
    """Lädt die historischen Marktdaten aus der SQLite-Datenbank."""
    conn = sqlite3.connect(DB_NAME)
    query = f"""
        SELECT date, close FROM market_data 
        WHERE symbol = '{symbol}' 
        AND date BETWEEN '{start_datum}' AND '{end_datum}'
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    df["date"] = pd.to_datetime(df["date"])
    df.set_index("date", inplace=True)
    return df

def berechne_rsi_strategie(df, fenster=14, overkauft=70, oversold=30):
    """Berechnet den RSI und generiert Kauf-/Verkaufsignale basierend auf den RSI-Werten."""
    # Berechnung der Differenzen
    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    
    # Berechnung der gleitenden Durchschnitte
    avg_gain = gain.rolling(window=fenster, min_periods=fenster).mean()
    avg_loss = loss.rolling(window=fenster, min_periods=fenster).mean()
    
    # Berechnung des RSI
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    df["RSI"] = rsi
    
    # Generiere Signale: 
    # Kaufen, wenn RSI < oversold; Verkaufen, wenn RSI > overkauft; sonst neutrale Position (0)
    df["signal"] = 0
    df.loc[df["RSI"] < oversold, "signal"] = 1
    df.loc[df["RSI"] > overkauft, "signal"] = -1
    
    return df

def visualisiere_rsi_strategie(df, symbol):
    """Visualisiert die Relative Strength (RSI) Strategie mit Plotly."""
    # Erstellen eines Subplot-Diagramms mit zwei Reihen (Preis und RSI)
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05,
                        subplot_titles=(f"{symbol} Preis", "RSI"))
    
    # Preisverlauf
    fig.add_trace(go.Scatter(x=df.index, y=df["close"], mode="lines", name="Schlusskurs"), row=1, col=1)
    
    # Kaufsignale (RSI < oversold)
    kauf_signale = df[df["signal"] == 1]
    fig.add_trace(go.Scatter(
        x=kauf_signale.index, y=kauf_signale["close"],
        mode="markers", marker=dict(color="green", size=8),
        name="Kaufen"
    ), row=1, col=1)
    
    # Verkaufssignale (RSI > overkauft)
    verkauf_signale = df[df["signal"] == -1]
    fig.add_trace(go.Scatter(
        x=verkauf_signale.index, y=verkauf_signale["close"],
        mode="markers", marker=dict(color="red", size=8),
        name="Verkaufen"
    ), row=1, col=1)
    
    # Darstellung des RSI
    fig.add_trace(go.Scatter(x=df.index, y=df["RSI"], mode="lines", name="RSI"), row=2, col=1)
    # Schwellenlinien für RSI
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
    
    fig.update_layout(title=f"Relative Strength (RSI) Strategie - {symbol}",
                      xaxis_title="Datum", yaxis_title="Preis")
    fig.show()

if __name__ == "__main__":
    symbol = "AAPL"
    df = lade_daten(symbol)
    df = berechne_rsi_strategie(df)
    visualisiere_rsi_strategie(df, symbol)

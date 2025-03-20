import sqlite3
import pandas as pd
import plotly.graph_objects as go

DB_NAME = "/Users/jennycao/AQM_Invesment/Backend/Datenbank/DB/investment.db"

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

def berechne_bollinger_bands(df, window=20, num_std=2):
    """
    Berechnet den gleitenden Durchschnitt und die Bollinger Bands.
    
    - window: Anzahl der Tage für den gleitenden Durchschnitt.
    - num_std: Multiplikator der Standardabweichung für die Berechnung der Bänder.
    
    Es werden auch Signale generiert:
      - Kaufsignal (1): Wenn der Schlusskurs unterhalb des unteren Bandes liegt.
      - Verkaufssignal (-1): Wenn der Schlusskurs oberhalb des oberen Bandes liegt.
      - Sonst: 0 (keine Aktion).
    """
    # Gleitender Durchschnitt und Standardabweichung
    df["MA"] = df["close"].rolling(window=window).mean()
    df["std"] = df["close"].rolling(window=window).std()
    
    # Obere und untere Bollinger Bands
    df["upper_band"] = df["MA"] + num_std * df["std"]
    df["lower_band"] = df["MA"] - num_std * df["std"]

    # Signal-Generierung
    df["signal"] = 0
    df.loc[df["close"] < df["lower_band"], "signal"] = 1   # Kaufsignal
    df.loc[df["close"] > df["upper_band"], "signal"] = -1  # Verkaufssignal
    
    return df

def visualisiere_bollinger_bands(df, symbol):
    """Visualisiert die Bollinger Bands Strategie mit Plotly."""
    fig = go.Figure()

    # Plot des Schlusskurses
    fig.add_trace(go.Scatter(x=df.index, y=df["close"], mode="lines", name="Schlusskurs"))
    # Plot des gleitenden Durchschnitts
    fig.add_trace(go.Scatter(x=df.index, y=df["MA"], mode="lines", name="MA"))
    # Obere Bollinger Band
    fig.add_trace(go.Scatter(
        x=df.index, y=df["upper_band"],
        mode="lines", name="Obere Band", line=dict(dash="dash", color="red")
    ))
    # Untere Bollinger Band
    fig.add_trace(go.Scatter(
        x=df.index, y=df["lower_band"],
        mode="lines", name="Untere Band", line=dict(dash="dash", color="green")
    ))

    # Markiere Signale
    kauf_signale = df[df["signal"] == 1]
    verkauf_signale = df[df["signal"] == -1]
    
    fig.add_trace(go.Scatter(
        x=kauf_signale.index, y=kauf_signale["close"],
        mode="markers", marker=dict(color="green", size=8),
        name="Kaufen"
    ))
    fig.add_trace(go.Scatter(
        x=verkauf_signale.index, y=verkauf_signale["close"],
        mode="markers", marker=dict(color="red", size=8),
        name="Verkaufen"
    ))

    fig.update_layout(title=f"Bollinger Bands Strategie - {symbol}",
                      xaxis_title="Datum", yaxis_title="Preis")
    fig.show()

if __name__ == "__main__":
    symbol = "AAPL"
    df = lade_daten(symbol)
    df = berechne_bollinger_bands(df)
    visualisiere_bollinger_bands(df, symbol)

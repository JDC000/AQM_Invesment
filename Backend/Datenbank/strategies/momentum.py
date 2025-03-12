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

def berechne_momentum_strategie(df, fenster=10):
    """Berechnet die Momentum-Strategie basierend auf Preisänderungen."""
    df["momentum"] = df["close"].diff(periods=fenster)
    df["signal"] = df["momentum"].apply(lambda x: 1 if x > 0 else -1)
    return df

def visualisiere_momentum_strategie(df, symbol):
    """Visualisiert die Strategie mit Plotly."""
    fig = go.Figure()

    # Kursverlauf
    fig.add_trace(go.Scatter(x=df.index, y=df["close"], mode="lines", name="Schlusskurs"))

    # Kaufsignale
    kauf_signale = df[df["signal"] == 1]
    fig.add_trace(go.Scatter(
        x=kauf_signale.index, y=kauf_signale["close"],
        mode="markers", marker=dict(color="green", size=8),
        name="Kaufen"
    ))

    # Verkaufssignale
    verkauf_signale = df[df["signal"] == -1]
    fig.add_trace(go.Scatter(
        x=verkauf_signale.index, y=verkauf_signale["close"],
        mode="markers", marker=dict(color="red", size=8),
        name="Verkaufen"
    ))

    fig.update_layout(title=f"Momentum-Strategie - {symbol}", xaxis_title="Datum", yaxis_title="Preis")
    fig.show()

if __name__ == "__main__":
    symbol = "AAPL"
    df = lade_daten(symbol)
    df = berechne_momentum_strategie(df)
    visualisiere_momentum_strategie(df, symbol)

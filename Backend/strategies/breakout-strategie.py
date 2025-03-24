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

def berechne_breakout_strategie(df, fenster=20):
    """
    Berechnet die Breakout-Strategie.
    Es werden das höchste und das niedrigste Kursniveau der vergangenen 'fenster'-Tage (ohne den aktuellen Tag) ermittelt.
    Ein Kaufsignal wird generiert, wenn der Schlusskurs über dem höchsten Kurs liegt,
    und ein Verkaufssignal, wenn er unter dem niedrigsten Kurs liegt.
    """
    # Berechnung der höchsten und niedrigsten Werte der letzten 'fenster' Tage (shift(1) vermeidet Lookahead-Bias)
    df["highest"] = df["close"].rolling(window=fenster).max().shift(1)
    df["lowest"] = df["close"].rolling(window=fenster).min().shift(1)
    
    # Generiere Signale: 1 für Kauf, -1 für Verkauf, 0 sonst
    df["signal"] = 0
    df.loc[df["close"] > df["highest"], "signal"] = 1
    df.loc[df["close"] < df["lowest"], "signal"] = -1
    
    return df

def visualisiere_breakout_strategie(df, symbol):
    """Visualisiert die Breakout-Strategie mit Plotly."""
    fig = go.Figure()

    # Plot des Schlusskurses
    fig.add_trace(go.Scatter(x=df.index, y=df["close"], mode="lines", name="Schlusskurs"))

    # Darstellung der höchsten und niedrigsten Niveaus (aus dem vorherigen Fenster)
    fig.add_trace(go.Scatter(
        x=df.index, y=df["highest"],
        mode="lines", name="Höchster Kurs (Vorperiode)",
        line=dict(dash="dash", color="orange")
    ))
    fig.add_trace(go.Scatter(
        x=df.index, y=df["lowest"],
        mode="lines", name="Niedrigster Kurs (Vorperiode)",
        line=dict(dash="dash", color="blue")
    ))

    # Markiere Kaufsignale
    kauf_signale = df[df["signal"] == 1]
    fig.add_trace(go.Scatter(
        x=kauf_signale.index, y=kauf_signale["close"],
        mode="markers", marker=dict(color="green", size=8),
        name="Kaufen"
    ))
    
    # Markiere Verkaufssignale
    verkauf_signale = df[df["signal"] == -1]
    fig.add_trace(go.Scatter(
        x=verkauf_signale.index, y=verkauf_signale["close"],
        mode="markers", marker=dict(color="red", size=8),
        name="Verkaufen"
    ))
    
    fig.update_layout(title=f"Breakout-Strategie - {symbol}",
                      xaxis_title="Datum", yaxis_title="Preis")
    fig.show()

if __name__ == "__main__":
    symbol = "AAPL"
    df = lade_daten(symbol)
    df = berechne_breakout_strategie(df)
    visualisiere_breakout_strategie(df, symbol)

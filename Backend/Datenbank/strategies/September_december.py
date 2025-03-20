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

def berechne_buy_september_sell_december_strategie(df):
    """
    Generiert Signale basierend auf saisonalen Mustern:
      - An dem ersten Handelstag im September wird ein Kaufsignal (1) gesetzt.
      - An dem ersten Handelstag im Dezember wird ein Verkaufssignal (-1) gesetzt.
      - Alle anderen Tage erhalten kein Signal (0).
    """
    df["signal"] = 0
    # Gruppiere nach Jahr und Monat, um den ersten Handelstag des jeweiligen Monats zu ermitteln.
    grouped = df.groupby([df.index.year, df.index.month])
    for (year, month), group in grouped:
        first_day = group.index.min()
        if month == 9:
            df.loc[first_day, "signal"] = 1
        elif month == 12:
            df.loc[first_day, "signal"] = -1
    return df

def visualisiere_buy_september_sell_december_strategie(df, symbol):
    """Visualisiert die saisonale Strategie mit Plotly."""
    fig = go.Figure()

    # Plot des Schlusskurses
    fig.add_trace(go.Scatter(x=df.index, y=df["close"], mode="lines", name="Schlusskurs"))

    # Markiere Kaufsignale (September)
    kauf_signale = df[df["signal"] == 1]
    fig.add_trace(go.Scatter(
        x=kauf_signale.index, y=kauf_signale["close"],
        mode="markers", marker=dict(color="green", size=10),
        name="Kaufen (September)"
    ))
    
    # Markiere Verkaufssignale (Dezember)
    verkauf_signale = df[df["signal"] == -1]
    fig.add_trace(go.Scatter(
        x=verkauf_signale.index, y=verkauf_signale["close"],
        mode="markers", marker=dict(color="red", size=10),
        name="Verkaufen (Dezember)"
    ))
    
    fig.update_layout(title=f"Buy September / Sell December Strategie - {symbol}",
                      xaxis_title="Datum", yaxis_title="Preis")
    fig.show()

if __name__ == "__main__":
    symbol = "AAPL"
    df = lade_daten(symbol)
    df = berechne_buy_september_sell_december_strategie(df)
    visualisiere_buy_september_sell_december_strategie(df, symbol)

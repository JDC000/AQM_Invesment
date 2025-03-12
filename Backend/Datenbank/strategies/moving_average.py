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

def berechne_ma_strategie(df, kurz_fenster=50, lang_fenster=200):
    """Berechnet die Kauf-/Verkaufsignale basierend auf Moving Averages."""
    df["MA_kurz"] = df["close"].rolling(window=kurz_fenster).mean()
    df["MA_lang"] = df["close"].rolling(window=lang_fenster).mean()
    df["signal"] = (df["MA_kurz"] > df["MA_lang"]).astype(int)  # 1: Kaufen, 0: Verkaufen
    return df

def visualisiere_ma_strategie(df, symbol):
    """Visualisiert die Moving Average Crossover-Strategie mit Plotly."""
    fig = go.Figure()

    # Kursverlauf
    fig.add_trace(go.Scatter(x=df.index, y=df["close"], mode="lines", name="Schlusskurs"))
    fig.add_trace(go.Scatter(x=df.index, y=df["MA_kurz"], mode="lines", name="MA 50"))
    fig.add_trace(go.Scatter(x=df.index, y=df["MA_lang"], mode="lines", name="MA 200"))

    # Kaufsignale
    kauf_signale = df[df["signal"] == 1]
    fig.add_trace(go.Scatter(
        x=kauf_signale.index, y=kauf_signale["close"],
        mode="markers", marker=dict(color="green", size=8),
        name="Kaufen"
    ))

    fig.update_layout(title=f"Moving Average Crossover - {symbol}", xaxis_title="Datum", yaxis_title="Preis")
    fig.show()

if __name__ == "__main__":
    symbol = "AAPL"
    df = lade_daten(symbol)
    df = berechne_ma_strategie(df)
    visualisiere_ma_strategie(df, symbol)

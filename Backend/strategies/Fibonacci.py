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

def berechne_fibonacci_strategie(df, fenster=50, tolerance=0.01):
    """
    Berechnet Fibonacci Retracement Levels basierend auf den höchsten und niedrigsten Kursen 
    der letzten 'fenster'-Tage und generiert Signale, wenn der Schlusskurs nahe an bestimmten 
    Fibonacci-Leveln liegt.
    
    Es werden folgende Fibonacci-Level berechnet:
      - 0% (Maximum)
      - 23,6%
      - 38,2%
      - 50%
      - 61,8%
      - 100% (Minimum)
      
    Signal:
      - Kaufsignal (1): wenn der Preis nahe am 38,2%-Level liegt
      - Verkaufssignal (-1): wenn der Preis nahe am 61,8%-Level liegt
      - Sonst: 0 (keine Aktion)
    """
    # Berechne rollierende Maxima und Minima (shift(1) vermeidet Lookahead-Bias)
    df["rolling_max"] = df["close"].rolling(window=fenster).max().shift(1)
    df["rolling_min"] = df["close"].rolling(window=fenster).min().shift(1)
    
    # Berechne den Preisbereich und die Differenz
    df["diff"] = df["rolling_max"] - df["rolling_min"]
    
    # Berechne die Fibonacci-Level
    df["fib_0"]   = df["rolling_max"]
    df["fib_23"]  = df["rolling_max"] - 0.236 * df["diff"]
    df["fib_38"]  = df["rolling_max"] - 0.382 * df["diff"]
    df["fib_50"]  = df["rolling_max"] - 0.5 * df["diff"]
    df["fib_62"]  = df["rolling_max"] - 0.618 * df["diff"]
    df["fib_100"] = df["rolling_min"]
    
    # Generiere Signale basierend auf der Nähe zu den Fibonacci-Leveln
    def get_signal(row):
        if pd.isna(row["fib_38"]) or pd.isna(row["fib_62"]):
            return 0
        # Prüfe, ob der Schlusskurs nahe am 38,2%-Level liegt (Kaufsignal)
        if abs(row["close"] - row["fib_38"]) / row["fib_38"] < tolerance:
            return 1
        # Prüfe, ob der Schlusskurs nahe am 61,8%-Level liegt (Verkaufssignal)
        elif abs(row["close"] - row["fib_62"]) / row["fib_62"] < tolerance:
            return -1
        else:
            return 0

    df["signal"] = df.apply(get_signal, axis=1)
    return df

def visualisiere_fibonacci_strategie(df, symbol):
    """Visualisiert die Fibonacci Strategie mit Plotly."""
    fig = go.Figure()

    # Plot des Schlusskurses
    fig.add_trace(go.Scatter(x=df.index, y=df["close"], mode="lines", name="Schlusskurs"))
    
    # Darstellung der Fibonacci-Level (hier werden 38,2% und 61,8% hervorgehoben)
    fig.add_trace(go.Scatter(x=df.index, y=df["fib_38"],
                             mode="lines", name="Fib 38,2%", line=dict(dash="dash", color="green")))
    fig.add_trace(go.Scatter(x=df.index, y=df["fib_62"],
                             mode="lines", name="Fib 61,8%", line=dict(dash="dash", color="red")))
    
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
    
    fig.update_layout(title=f"Fibonacci Strategie - {symbol}",
                      xaxis_title="Datum", yaxis_title="Preis")
    fig.show()

if __name__ == "__main__":
    symbol = "AAPL"
    df = lade_daten(symbol)
    df = berechne_fibonacci_strategie(df)
    visualisiere_fibonacci_strategie(df, symbol)

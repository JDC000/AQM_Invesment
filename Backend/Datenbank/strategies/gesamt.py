import sqlite3
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

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

def berechne_kombinierte_strategie(df):
    """
    Berechnet einzelne Signale aus den bisherigen Strategien und kombiniert sie zu einem Gesamtsignal.
    
    Folgende Einzelsignale werden berechnet:
      - Momentum: Differenz des Schlusskurses über ein Fenster (Standard: 10 Tage).
      - Moving Average: Kurzer (50 Tage) vs. langer (200 Tage) gleitender Durchschnitt.
      - RSI: Relative Strength Index (Fenster 14; Kauf bei < 30, Verkauf bei > 70).
      - Breakout: Signal, wenn der Schlusskurs über dem höchsten bzw. unter dem niedrigsten Kurs
                  der letzten 20 Tage (ohne aktuellen Tag) liegt.
      - Fibonacci: Signal, wenn der Preis nahe an den berechneten Fibonacci-Retracement-Leveln (38,2 % bzw. 61,8 %) liegt.
      - Bollinger Bands: Signal, wenn der Schlusskurs unter das untere oder über das obere Bollinger Band fällt.
      - Saisonale Strategie: Kaufsignal am ersten Handelstag im September, Verkaufssignal im Dezember.
      
    Das Gesamtsignal wird als Summe der einzelnen Signale berechnet. Liegt die Summe über 0, wird gekauft (1),
    liegt sie unter 0, wird verkauft (-1), ansonsten wird keine Aktion empfohlen (0).
    """
    # --- Momentum Strategie ---
    fenster_momentum = 10
    df["momentum"] = df["close"].diff(periods=fenster_momentum)
    # Wenn momentum > 0: 1, sonst -1 (sofern Wert vorhanden)
    df["signal_momentum"] = df["momentum"].apply(lambda x: 1 if pd.notna(x) and x > 0 else (-1 if pd.notna(x) else 0))
    
    # --- Moving Average Strategie ---
    kurz_fenster = 50
    lang_fenster = 200
    df["MA_kurz"] = df["close"].rolling(window=kurz_fenster).mean()
    df["MA_lang"] = df["close"].rolling(window=lang_fenster).mean()
    df["signal_ma"] = 0
    # Wenn MA_kurz > MA_lang: Kaufsignal, ansonsten Verkaufssignal (sofern beide vorhanden)
    df.loc[(df["MA_kurz"] > df["MA_lang"]) & df["MA_lang"].notna(), "signal_ma"] = 1
    df.loc[(df["MA_kurz"] < df["MA_lang"]) & df["MA_lang"].notna(), "signal_ma"] = -1

    # --- RSI Strategie ---
    rsi_fenster = 14
    oversold = 30
    overbought = 70
    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=rsi_fenster, min_periods=rsi_fenster).mean()
    avg_loss = loss.rolling(window=rsi_fenster, min_periods=rsi_fenster).mean()
    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))
    df["signal_rsi"] = 0
    df.loc[df["RSI"] < oversold, "signal_rsi"] = 1
    df.loc[df["RSI"] > overbought, "signal_rsi"] = -1

    # --- Breakout Strategie ---
    breakout_fenster = 20
    df["highest"] = df["close"].rolling(window=breakout_fenster).max().shift(1)
    df["lowest"] = df["close"].rolling(window=breakout_fenster).min().shift(1)
    df["signal_breakout"] = 0
    df.loc[df["close"] > df["highest"], "signal_breakout"] = 1
    df.loc[df["close"] < df["lowest"], "signal_breakout"] = -1

    # --- Fibonacci Strategie ---
    fib_fenster = 50
    tolerance = 0.01
    df["rolling_max"] = df["close"].rolling(window=fib_fenster).max().shift(1)
    df["rolling_min"] = df["close"].rolling(window=fib_fenster).min().shift(1)
    df["diff"] = df["rolling_max"] - df["rolling_min"]
    df["fib_38"] = df["rolling_max"] - 0.382 * df["diff"]
    df["fib_62"] = df["rolling_max"] - 0.618 * df["diff"]
    def fib_signal(row):
        if pd.isna(row["fib_38"]) or pd.isna(row["fib_62"]):
            return 0
        if abs(row["close"] - row["fib_38"]) / row["fib_38"] < tolerance:
            return 1
        elif abs(row["close"] - row["fib_62"]) / row["fib_62"] < tolerance:
            return -1
        else:
            return 0
    df["signal_fib"] = df.apply(fib_signal, axis=1)

    # --- Bollinger Bands Strategie ---
    boll_window = 20
    num_std = 2
    df["MA_boll"] = df["close"].rolling(window=boll_window).mean()
    df["std_boll"] = df["close"].rolling(window=boll_window).std()
    df["upper_band"] = df["MA_boll"] + num_std * df["std_boll"]
    df["lower_band"] = df["MA_boll"] - num_std * df["std_boll"]
    df["signal_bollinger"] = 0
    df.loc[df["close"] < df["lower_band"], "signal_bollinger"] = 1
    df.loc[df["close"] > df["upper_band"], "signal_bollinger"] = -1

    # --- Saisonale Strategie: Buy in September, Sell in December ---
    df["signal_season"] = 0
    # Gruppiere nach Jahr und Monat, ermittle den ersten Handelstag im jeweiligen Monat.
    grouped = df.groupby([df.index.year, df.index.month])
    for (year, month), group in grouped:
        first_day = group.index.min()
        if month == 9:
            df.loc[first_day, "signal_season"] = 1
        elif month == 12:
            df.loc[first_day, "signal_season"] = -1

    # --- Kombination der Signale ---
    signal_cols = ["signal_momentum", "signal_ma", "signal_rsi", "signal_breakout",
                   "signal_fib", "signal_bollinger", "signal_season"]
    df["signal_sum"] = df[signal_cols].sum(axis=1)
    # Gesamtsignal: > 0 => Kaufen (1), < 0 => Verkaufen (-1), sonst 0
    df["signal_combined"] = df["signal_sum"].apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
    
    return df

def visualisiere_kombinierte_strategie(df, symbol):
    """Visualisiert die kombinierte Strategie mit Plotly."""
    fig = go.Figure()

    # Kursverlauf plotten
    fig.add_trace(go.Scatter(x=df.index, y=df["close"], mode="lines", name="Schlusskurs"))
    
    # Gesamtsignale als Marker darstellen
    kauf_signale = df[df["signal_combined"] == 1]
    verkauf_signale = df[df["signal_combined"] == -1]
    
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
    
    fig.update_layout(title=f"Kombinierte Strategie - {symbol}",
                      xaxis_title="Datum", yaxis_title="Preis")
    fig.show()

if __name__ == "__main__":
    symbol = "AAPL"
    df = lade_daten(symbol)
    df = berechne_kombinierte_strategie(df)
    visualisiere_kombinierte_strategie(df, symbol)

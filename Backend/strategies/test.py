import pandas as pd
import plotly.graph_objects as go
import sqlite3

import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "DB", "investment.db")

def lade_daten_aus_db(symbol, start_datum="2010-01-01", end_datum="2020-12-31", db_pfad=DB_NAME):
    conn = sqlite3.connect(db_pfad)
    abfrage = """
        SELECT date, close
        FROM market_data
        WHERE symbol = ? AND date BETWEEN ? AND ?
        ORDER BY date
    """
    df = pd.read_sql_query(abfrage, conn, params=[symbol, start_datum, end_datum], parse_dates=["date"])
    conn.close()
    return df


def run_strategy(df: pd.DataFrame, kurz_fenster=50, lang_fenster=200, start_kapital=100000):
    df = df.copy()
    df["SMA_kurz"] = df["close"].rolling(window=kurz_fenster).mean()
    df["SMA_lang"] = df["close"].rolling(window=lang_fenster).mean()

    # === Bestimme die genauen Schnittsignale ===
    df["ma_diff"] = df["SMA_kurz"] - df["SMA_lang"]
    df["ma_diff_prev"] = df["ma_diff"].shift(1)

    df["signal"] = 0
    df.loc[(df["ma_diff"] > 0) & (df["ma_diff_prev"] <= 0), "signal"] = 1   # Kaufen
    df.loc[(df["ma_diff"] < 0) & (df["ma_diff_prev"] >= 0), "signal"] = -1  # Verkaufen

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

    # Diagramm 1: Preis, SMA, Kauf/Verkauf Punkte ===
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=df["date"], y=df["close"], name="Aktienkurs", line=dict(color="gray")))
    fig1.add_trace(go.Scatter(x=df["date"], y=df["SMA_kurz"], name=f"SMA {kurz_fenster}", line=dict(color="blue")))
    fig1.add_trace(go.Scatter(x=df["date"], y=df["SMA_lang"], name=f"SMA {lang_fenster}", line=dict(color="orange")))

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
        title="MA Crossover Strategie – Kauf/Verkauf Signale",
        xaxis_title="Datum", yaxis_title="Aktienkurs (€)"
    )

    # === Diagramm 2: Gesamtvermögen ===
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
        title="💰 Gesamtvermögen nach jeder Transaktion",
        xaxis_title="Datum", yaxis_title="Vermögen (€)"
    )

    return fig1, fig2, gesamtwert, gewinn


# === DIREKT AUSFÜHREN ===
if __name__ == "__main__":
    symbol = "AAPL"  # oder DAI, ATOM, etc.
    df = lade_daten_aus_db(symbol)

    if df.empty:
        print(f"Keine Daten für das Symbol '{symbol}' in der DB.")
    else:
        fig1, fig2, gesamt, gewinn = run_strategy(df)
        print(f"Gesamtvermögen am Ende: €{gesamt:,.2f}")
        print(f"Gewinn: €{gewinn:,.2f}")
        fig1.show()
        #fig2.show()

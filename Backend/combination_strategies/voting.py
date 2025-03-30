import sys
import os
import sqlite3
import pandas as pd
import itertools
import numpy as np
import plotly.graph_objects as go

# Füge den übergeordneten Ordner zum Suchpfad hinzu, damit Module aus dem Projekt-Root gefunden werden
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from Datenbank.api import get_available_stocks, load_stock_data

# ---------------------------
# Hilfsfunktionen
# ---------------------------
def ensure_close_column(df):
    """
    Stellt sicher, dass das DataFrame die Spalte 'close' enthält.
    Falls stattdessen 'Price' vorhanden ist, wird diese umbenannt.
    """
    if "close" not in df.columns:
        if "Price" in df.columns:
            df = df.rename(columns={"Price": "close"})
        else:
            raise ValueError("Das DataFrame enthält weder 'close' noch 'Price'")
    return df

def ensure_datetime_index(df):
    """
    Stellt sicher, dass der Index des DataFrames ein DatetimeIndex ist.
    Falls nicht, wird versucht, den Index zu konvertieren.
    """
    if not isinstance(df.index, pd.DatetimeIndex):
        try:
            df.index = pd.to_datetime(df.index)
        except Exception as e:
            raise ValueError("Index konnte nicht in datetime konvertiert werden: " + str(e))
    return df

def format_currency(value):
    """
    Formatiert einen Zahlenwert als Währung.
    Beispiel: 100000 -> "100.000,00"
    """
    s = f"{value:,.2f}"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return s

def filter_stocks(tickers):
    """
    Filtert die Tickerliste, sodass nur Aktien (Stocks) enthalten sind.
    ETFs und Cryptos werden ausgeklammert.
    """
    ETFS = {"XFI", "XIT", "XLB", "XLE", "XLF", "XLI", "XLP", "XLU", "XLV", "XLY", "XSE", "VT"}
    CRYPTOS = {"BNB", "XRP", "SOL", "DOT", "LTC", "USDC", "LINK", "BCH", "XLM", "UNI",
               "ATOM", "TRX", "ETC", "NEAR", "XMR", "VET", "EOS", "FIL", "CRO", "DAI", "DASH", "ENJ"}
    return [ticker for ticker in tickers if ticker not in ETFS and ticker not in CRYPTOS]

def save_results(average_results, traded_stocks, start_date, end_date, output_path):
    """
    Speichert die Ergebnisse für jeden Vote‑Threshold in einer Textdatei.
    Für jeden Schwellenwert wird ein eigener Abschnitt mit aggregierten Kennzahlen
    sowie den Ergebnissen pro Aktie angehängt.
    """
    results_lines = []
    results_lines.append(f"Handelszeitraum: {start_date} bis {end_date}\n")
    results_lines.append(f"Gehandelte Aktien: {', '.join(traded_stocks)}\n\n")
    
    results_lines.append("Ergebnisse für verschiedene Vote‑Thresholds:\n")
    results_lines.append("============================================\n\n")
    
    # Für jeden Vote‑Threshold werden die aggregierten Kennzahlen geschrieben
    for vt in sorted(average_results.keys()):
        data = average_results[vt]
        results_lines.append(f"Vote‑Threshold = {vt}\n")
        results_lines.append("--------------------------------------------\n")
        results_lines.append(f"  Durchschnittlicher Endwert: €{format_currency(data['avg_final'])}\n")
        results_lines.append(f"  Durchschnittlicher Gewinn: €{format_currency(data['avg_profit'])}\n")
        results_lines.append(f"  Durchschnittliche Veränderung: {format_currency(data['avg_percent'])} %\n\n")
        
        results_lines.append("  Ergebnisse pro Aktie:\n")
        for ticker, res in data["details"].items():
            results_lines.append(f"    {ticker}: Endwert = €{format_currency(res['final_value'])}, "
                                 f"Gewinn = €{format_currency(res['profit'])}, "
                                 f"Veränderung = {format_currency(res['percent'])} %\n")
        results_lines.append("\n")
    
    # Ermittele und logge den besten Vote‑Threshold (basierend auf durchschnittlichem Endwert)
    best_vt = max(average_results.items(), key=lambda x: x[1]['avg_final'])[0]
    best_data = average_results[best_vt]
    results_lines.append("Beste Vote‑Threshold (basierend auf durchschnittlichem Endwert):\n")
    results_lines.append("============================================\n")
    results_lines.append(f"  Vote‑Threshold = {best_vt}\n")
    results_lines.append(f"  Durchschnittlicher Endwert: €{format_currency(best_data['avg_final'])}\n")
    results_lines.append(f"  Durchschnittlicher Gewinn: €{format_currency(best_data['avg_profit'])}\n")
    results_lines.append(f"  Durchschnittliche Veränderung: {format_currency(best_data['avg_percent'])} %\n\n")
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(results_lines)
    
    print(f"Ergebnisse wurden in '{output_path}' gespeichert.")

# ---------------------------
# Voting-Strategie
# ---------------------------
def get_signals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Berechnet für jede Strategie die Handelssignale und gibt ein DataFrame zurück,
    in dem jede Spalte ein Signal einer Strategie enthält.
    Signalwerte: 1 = Kaufen, -1 = Verkaufen, 0 = keine Aktion
    """
    df_signals = pd.DataFrame(index=df.index)

    # 1. Bollinger Bands Strategie
    window = 20
    num_std = 2
    boll_df = df.copy()
    boll_df["MA"] = boll_df["close"].rolling(window=window).mean()
    boll_df["std"] = boll_df["close"].rolling(window=window).std()
    boll_df["upper_band"] = boll_df["MA"] + num_std * boll_df["std"]
    boll_df["lower_band"] = boll_df["MA"] - num_std * boll_df["std"]
    boll_df["signal"] = 0
    boll_df.loc[boll_df["close"] < boll_df["lower_band"], "signal"] = 1
    boll_df.loc[boll_df["close"] > boll_df["upper_band"], "signal"] = -1
    df_signals["bollinger"] = boll_df["signal"]

    # 2. Breakout-Strategie
    fenster = 20
    breakout_df = df.copy()
    breakout_df["highest"] = breakout_df["close"].rolling(window=fenster).max().shift(1)
    breakout_df["lowest"] = breakout_df["close"].rolling(window=fenster).min().shift(1)
    breakout_df["signal"] = 0
    breakout_df.loc[breakout_df["close"] > breakout_df["highest"], "signal"] = 1
    breakout_df.loc[breakout_df["close"] < breakout_df["lowest"], "signal"] = -1
    df_signals["breakout"] = breakout_df["signal"]

    # 3. Buy and Hold Strategie
    bah_df = df.copy()
    bah_df["signal"] = 0
    if not bah_df.empty:
        bah_df.iloc[0, bah_df.columns.get_loc("signal")] = 1
        bah_df.iloc[-1, bah_df.columns.get_loc("signal")] = -1
    df_signals["buy_hold"] = bah_df["signal"]

    # 4. Momentum-Strategie
    window_m = 20
    momentum_df = df.copy()
    momentum_df['Momentum'] = momentum_df['close'] / momentum_df['close'].shift(window_m) - 1
    momentum_df['signal'] = ((momentum_df['Momentum'] > 0) &
                             (momentum_df['Momentum'] > momentum_df['Momentum'].shift(1))).astype(int)
    momentum_df['signal'] = momentum_df['signal'].replace(0, -1)
    df_signals["momentum"] = momentum_df["signal"]

    # 5. MA Crossover Strategie
    kurz_fenster = 50
    lang_fenster = 200
    mac_df = df.copy()
    mac_df["SMA_kurz"] = mac_df["close"].rolling(window=kurz_fenster).mean()
    mac_df["SMA_lang"] = mac_df["close"].rolling(window=lang_fenster).mean()
    mac_df["ma_diff"] = mac_df["SMA_kurz"] - mac_df["SMA_lang"]
    mac_df["ma_diff_prev"] = mac_df["ma_diff"].shift(1)
    mac_df["signal"] = 0
    mac_df.loc[(mac_df["ma_diff"] > 0) & (mac_df["ma_diff_prev"] <= 0), "signal"] = 1
    mac_df.loc[(mac_df["ma_diff"] < 0) & (mac_df["ma_diff_prev"] >= 0), "signal"] = -1
    df_signals["ma_crossover"] = mac_df["signal"]

    # 6. RSI Strategie
    fenster_rsi = 14
    overkauft = 70
    oversold = 30
    rsi_df = df.copy()
    delta = rsi_df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=fenster_rsi, min_periods=fenster_rsi).mean()
    avg_loss = loss.rolling(window=fenster_rsi, min_periods=fenster_rsi).mean()
    rs = avg_gain / avg_loss
    rsi_df["RSI"] = 100 - (100 / (1 + rs))
    rsi_df["signal"] = 0
    rsi_df.loc[rsi_df["RSI"] < oversold, "signal"] = 1
    rsi_df.loc[rsi_df["RSI"] > overkauft, "signal"] = -1
    df_signals["rsi"] = rsi_df["signal"]

    # 7. Buy-September / Sell-December Strategie
    seasonal_df = df.copy()
    if "date" in seasonal_df.columns:
        seasonal_df.set_index("date", inplace=True)
    if not isinstance(seasonal_df.index, pd.DatetimeIndex):
        seasonal_df.index = pd.to_datetime(seasonal_df.index)
    seasonal_df.index = seasonal_df.index.normalize()
    seasonal_df["signal"] = 0
    grouped = seasonal_df.groupby([seasonal_df.index.year, seasonal_df.index.month])
    for (year, month), group in grouped:
        first_day = group.index.min()
        if month == 9:
            seasonal_df.loc[first_day, "signal"] = 1
        elif month == 12:
            seasonal_df.loc[first_day, "signal"] = -1
    seasonal_df = seasonal_df.reindex(df.index, method="ffill")
    df_signals["seasonal"] = seasonal_df["signal"]

    return df_signals

def run_voting_strategy(df: pd.DataFrame, vote_threshold: int = 5, start_kapital: float = 100000):
    """
    Aggregiert die Signale der einzelnen Strategien und generiert ein kombiniertes Handelssignal.
    
    Parameter:
      - df: DataFrame mit historischen Kursdaten (muss mindestens die Spalte 'close' enthalten)
      - vote_threshold: Mindestanzahl an Strategien, die ein Kauf- bzw. Verkaufssignal liefern müssen,
        damit das Gesamtsignal 1 bzw. -1 beträgt.
      - start_kapital: Startkapital für die Handelssimulation
    
    Rückgabe:
      - fig1: Plotly-Figur mit dem Kurschart und den Kauf-/Verkaufspunkten der Voting-Strategie
      - fig2: Plotly-Figur der Equity-Kurve
      - final_value: Endkapital der Simulation
      - signals: DataFrame mit den einzelnen Strategie-Signalen und dem kombinierten Signal
    """
    signals = get_signals(df)
    signals["buy_count"] = (signals == 1).sum(axis=1)
    signals["sell_count"] = (signals == -1).sum(axis=1)
    signals["combined_signal"] = np.where(signals["buy_count"] > signals["sell_count"], 1,
                                      np.where(signals["sell_count"] > signals["buy_count"], -1, 0))
    signals.loc[signals["buy_count"] >= vote_threshold, "combined_signal"] = 1
    signals.loc[signals["sell_count"] >= vote_threshold, "combined_signal"] = -1

    kapital = start_kapital
    position = 0
    equity_curve = []
    combined_signals = signals["combined_signal"]
    for i in range(len(df)):
        preis = df.iloc[i]["close"]
        signal = combined_signals.iloc[i]
        if signal == 1 and position == 0:
            position = kapital / preis
            kapital = 0
        elif signal == -1 and position > 0:
            kapital = position * preis
            position = 0
        equity_curve.append(kapital + position * preis)
    final_value = equity_curve[-1] if equity_curve else start_kapital

    x_values = df["date"] if "date" in df.columns else df.index

    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=x_values, y=df["close"], mode="lines", name="Schlusskurs"))
    buy_signals = signals[signals["combined_signal"] == 1]
    sell_signals = signals[signals["combined_signal"] == -1]
    fig1.add_trace(go.Scatter(x=buy_signals.index, y=df.loc[buy_signals.index, "close"],
                              mode="markers", marker=dict(color="green", size=8), name="Kaufen"))
    fig1.add_trace(go.Scatter(x=sell_signals.index, y=df.loc[sell_signals.index, "close"],
                              mode="markers", marker=dict(color="red", size=8), name="Verkaufen"))
    fig1.update_layout(title="Voting-Mechanismus: Aggregierte Strategie",
                       xaxis_title="Datum", yaxis_title="Preis", xaxis_type="date")

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=x_values, y=equity_curve, mode="lines", name="Equity"))
    fig2.update_layout(title="Kapitalentwicklung der Voting-Strategie",
                       xaxis_title="Datum", yaxis_title="Kapital", xaxis_type="date")

    return fig1, fig2, final_value, signals

# ---------------------------
# Backtest über alle Aktien in einem Zeitraum für verschiedene Vote‑Thresholds
# ---------------------------
def run_for_period(start_date, end_date, output_path):
    """
    Führt den Voting-Backtest für den angegebenen Zeitraum aus, indem alle (gefilterten) Aktien
    aus der Datenbank geladen und die Voting-Strategie für verschiedene Vote‑Thresholds angewendet werden.
    Die Ergebnisse (Endwert, Gewinn und prozentuale Veränderung) werden pro Aktie und pro Threshold
    sowie aggregiert gespeichert.
    """
    print(f"\n*** Starte Voting-Backtest für Zeitraum: {start_date} bis {end_date} ***")
    available_tickers = get_available_stocks()
    if not available_tickers:
        print("Keine Ticker verfügbar!")
        return

    tickers_to_test = filter_stocks(available_tickers)
    if not tickers_to_test:
        print("Nach Filterung sind keine Aktien (Stocks) verfügbar!")
        return
    print(f"Verarbeite Voting-Strategie für die Ticker: {', '.join(tickers_to_test)}")

    start_kapital = 100000
    vote_thresholds = [1, 2, 3, 4, 5]
    results_per_threshold = {vt: {} for vt in vote_thresholds}

    for ticker in tickers_to_test:
        print(f"\nBearbeite Ticker: {ticker}")
        try:
            df = load_stock_data(ticker, start_date, end_date)
            df = ensure_close_column(df)
            df = ensure_datetime_index(df)
            if "date" in df.columns:
                df.set_index("date", inplace=True)
                df.index = df.index.normalize()
        except Exception as e:
            print(f"Fehler beim Laden der Daten für {ticker}: {e}")
            continue

        for vt in vote_thresholds:
            try:
                fig1, fig2, final_value, _ = run_voting_strategy(df, vote_threshold=vt, start_kapital=start_kapital)
                profit = final_value - start_kapital
                percent = (profit / start_kapital) * 100
                results_per_threshold[vt][ticker] = {"final_value": final_value, "profit": profit, "percent": percent}
                print(f"{ticker} (Threshold {vt}): Endwert = {final_value:,.2f}, Gewinn = {profit:,.2f}, Veränderung = {percent:.2f} %")
            except Exception as e:
                print(f"Fehler bei der Voting-Strategie für {ticker} mit Threshold {vt}: {e}")
                continue

    if not any(results_per_threshold.values()):
        print("Für diesen Zeitraum wurden keine Ergebnisse erzielt!")
        return

    average_results = {}
    for vt, res in results_per_threshold.items():
        if res:
            n = len(res)
            avg_final = sum(r["final_value"] for r in res.values()) / n
            avg_profit = sum(r["profit"] for r in res.values()) / n
            avg_percent = sum(r["percent"] for r in res.values()) / n
            average_results[vt] = {
                "avg_final": avg_final,
                "avg_profit": avg_profit,
                "avg_percent": avg_percent,
                "details": res
            }
            print(f"\nVote‑Threshold {vt}:")
            print(f"  Durchschnittlicher Endwert = €{format_currency(avg_final)}")
            print(f"  Durchschnittlicher Gewinn = €{format_currency(avg_profit)}")
            print(f"  Durchschnittliche Veränderung = {format_currency(avg_percent)} %")
        else:
            average_results[vt] = {
                "avg_final": 0,
                "avg_profit": 0,
                "avg_percent": 0,
                "details": {}
            }
            print(f"\nVote‑Threshold {vt}: Keine Ergebnisse.")

    save_results(average_results, list(tickers_to_test), start_date, end_date, output_path)

# ---------------------------
# Main-Funktion: Verschiedene Zeiträume durchlaufen
# ---------------------------
def main():
    date_periods = {
        "2012_2023": ("2012-01-01", "2023-12-31"),
        "2012_2017": ("2012-01-01", "2017-12-31"),
        "2018_2023": ("2018-01-01", "2023-12-31")
    }

    for label, (start_date, end_date) in date_periods.items():
        output_file = f"results_voting_{label}.txt"
        run_for_period(start_date, end_date, output_file)

if __name__ == "__main__":
    main()


import sys
import os
import pandas as pd
import warnings

# Unterdrücke FutureWarnings (sollte nur als temporäre Maßnahme genutzt werden)
warnings.simplefilter(action="ignore", category=FutureWarning)

# Erweitere den Pfad, damit Module aus dem übergeordneten Verzeichnis gefunden werden
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from Datenbank.api import get_available_stocks, load_stock_data
from strategies import STRATEGIES

def ensure_close_column(df):
    """
    Überprüft, ob das DataFrame die Spalte 'close' enthält.
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
    Falls nicht, wird versucht, den Index in einen DatetimeIndex zu konvertieren.
    """
    if not isinstance(df.index, pd.DatetimeIndex):
        try:
            df.index = pd.to_datetime(df.index)
        except Exception as e:
            raise ValueError("Index konnte nicht in datetime konvertiert werden: " + str(e))
    return df

def calculate_buy_and_hold_performance(df, start_kapital):
    """
    Berechnet die Buy-&-Hold-Performance:
    - Startpreis entspricht dem ersten 'close'-Wert,
    - Endpreis dem letzten 'close'-Wert.
    Es wird der Endkapitalwert sowie der prozentuale Gewinn zurückgegeben.
    """
    start_price = df.iloc[0]["close"]
    end_price = df.iloc[-1]["close"]
    total = start_kapital * (end_price / start_price)
    percent_gain = (total - start_kapital) / start_kapital * 100
    return total, percent_gain

def filter_stocks(tickers):
    """
    Filtert die Tickerliste, sodass nur Aktien (Stocks) enthalten sind.
    Folgende ETFs und Cryptos werden ausgelassen:
      ETFS = {"XFI", "XIT", "XLB", "XLE", "XLF", "XLI", "XLP", "XLU", "XLV", "XLY", "XSE"}
      CRYPTOS = {"BNB", "XRP", "SOL", "DOT", "LTC", "USDC", "LINK", "BCH", "XLM", "UNI",
                 "ATOM", "TRX", "ETC", "NEAR", "XMR", "VET", "EOS", "FIL", "CRO", "DAI", "DASH", "ENJ"}
    VT wird hier absichtlich nicht mit aufgenommen, damit die Strategien nicht darauf angewendet werden.
    """
    ETFS = {"XFI", "XIT", "XLB", "XLE", "XLF", "XLI", "XLP", "XLU", "XLV", "XLY", "XSE"}
    CRYPTOS = {"BNB", "XRP", "SOL", "DOT", "LTC",
               "USDC", "LINK", "BCH", "XLM", "UNI", "ATOM", "TRX",
               "ETC", "NEAR", "XMR", "VET", "EOS", "FIL", "CRO", "DAI", "DASH", "ENJ"}
    return [ticker for ticker in tickers if ticker not in ETFS and ticker not in CRYPTOS]

def main():
    # Alle verfügbaren Ticker abrufen
    available_tickers = get_available_stocks()
    if not available_tickers:
        print("Keine Ticker verfügbar!")
        return

    # Filtere nur die Stocks (ohne ETFs, Cryptos und VT)
    tickers_to_test = filter_stocks(available_tickers)
    if not tickers_to_test:
        print("Nach Filterung sind keine Aktien (Stocks) verfügbar!")
        return
    print(f"Vergleiche Strategien für die Ticker: {', '.join(tickers_to_test)}")

    # Zeitraum und Startkapital für den Backtest (anpassbar)
    start_date = "2018-01-01"
    end_date = "2023-12-31"
    start_kapital = 100000

    # Ergebnis-Dictionary zur Speicherung der Performance jeder Strategie pro Ticker
    results = {strategy_name: {"totals": [], "profits": []} for strategy_name in STRATEGIES.keys()}

    # Iteriere über alle ausgewählten Ticker und wende die Strategien an
    for ticker in tickers_to_test:
        print(f"\nBearbeite Ticker: {ticker}")
        try:
            df = load_stock_data(ticker, start_date, end_date)
            df = ensure_close_column(df)
            df = ensure_datetime_index(df)
        except Exception as e:
            print(f"Fehler beim Laden der Daten für {ticker}: {e}")
            continue

        for strategy_name, run_strategy in STRATEGIES.items():
            try:
                # Erwartet: (fig1, fig2, total, profit)
                fig1, fig2, total, profit = run_strategy(df, start_kapital=start_kapital)
                percent_gain = (total - start_kapital) / start_kapital * 100
                results[strategy_name]["totals"].append(total)
                results[strategy_name]["profits"].append(percent_gain)
                print(f"  {strategy_name}: Gesamtwert = {total:,.2f} €, Prozentualer Gewinn = {percent_gain:,.2f} %")
            except Exception as e:
                print(f"  Fehler bei der Strategie '{strategy_name}' für {ticker}: {e}")

    # Durchschnittliche Performance pro Strategie berechnen
    average_results = {}
    for strategy_name, data in results.items():
        totals = [t for t in data["totals"] if t is not None]
        profits = [p for p in data["profits"] if p is not None]
        avg_total = sum(totals) / len(totals) if totals else None
        avg_profit = sum(profits) / len(profits) if profits else None
        average_results[strategy_name] = {"avg_total": avg_total, "avg_profit": avg_profit}

    print("\nDurchschnittliche Performance pro Strategie:")
    for strategy_name, metrics in average_results.items():
        if metrics["avg_total"] is not None:
            print(f"  {strategy_name}: Durchschnittlicher Gesamtwert = {metrics['avg_total']:,.2f} €, "
                  f"Durchschnittlicher prozentualer Gewinn = {metrics['avg_profit']:,.2f} %")
        else:
            print(f"  {strategy_name}: Keine gültigen Ergebnisse.")

    # Beste Strategie basierend auf dem durchschnittlichen Gesamtwert ermitteln
    best_strategy = None
    best_avg_total = -float("inf")
    for strategy_name, metrics in average_results.items():
        if metrics["avg_total"] is not None and metrics["avg_total"] > best_avg_total:
            best_avg_total = metrics["avg_total"]
            best_strategy = strategy_name

    print("\nBeste Strategie (basierend auf durchschnittlichem Gesamtwert):")
    if best_strategy:
        print(f"{best_strategy} mit einem durchschnittlichen Gesamtwert von {best_avg_total:,.2f} €")
    else:
        print("Keine Strategie konnte erfolgreich ausgewertet werden.")

    # VT als Vergleich: Abruf genau wie bei den anderen Ticker
    vt_total, vt_profit = None, None
    try:
        print("\nVergleiche mit VT (ETF) per Buy & Hold:")
        vt_df = load_stock_data("VT", start_date, end_date)
        vt_df = ensure_close_column(vt_df)
        vt_df = ensure_datetime_index(vt_df)
        vt_total, vt_profit = calculate_buy_and_hold_performance(vt_df, start_kapital)
        print(f"  VT: Gesamtwert = {vt_total:,.2f} €, Prozentualer Gewinn = {vt_profit:,.2f} %")
    except Exception as e:
        print(f"Fehler beim Laden der Daten für VT: {e}")

    # Ergebnisse in eine Textdatei schreiben
    results_lines = []
    results_lines.append(f"Handelszeitraum: {start_date} bis {end_date}\n")
    results_lines.append(f"Verwendete Aktien: {', '.join(tickers_to_test)}\n\n")
    results_lines.append("Ergebnisse pro Strategie:\n")
    for strategy_name, metrics in average_results.items():
        if metrics["avg_total"] is not None:
            results_lines.append(
                f"  {strategy_name}: Durchschnittlicher Gesamtwert = {metrics['avg_total']:,.2f} €, "
                f"Durchschnittlicher prozentualer Gewinn = {metrics['avg_profit']:,.2f} %\n"
            )
        else:
            results_lines.append(f"  {strategy_name}: Keine gültigen Ergebnisse.\n")
    results_lines.append("\nBeste Strategie (basierend auf durchschnittlichem Gesamtwert):\n")
    if best_strategy:
        results_lines.append(f"  {best_strategy} mit einem durchschnittlichen Gesamtwert von {best_avg_total:,.2f} €\n")
    else:
        results_lines.append("  Keine Strategie konnte erfolgreich ausgewertet werden.\n")
    results_lines.append("\nBuy & Hold Vergleich (VT):\n")
    if vt_total is not None and vt_profit is not None:
        results_lines.append(f"  VT: Gesamtwert = {vt_total:,.2f} €, Prozentualer Gewinn = {vt_profit:,.2f} %\n")
    else:
        results_lines.append("  VT-Daten konnten nicht geladen werden.\n")

    # Schreibe die Ergebnisse in eine neue Datei (überschreibt bei jedem Lauf)
    with open("results_vergleich.txt", "w", encoding="utf-8") as f:
        f.writelines(results_lines)

if __name__ == "__main__":
    main()

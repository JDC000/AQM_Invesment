import sys
import os
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

def main():
    # Alle verfügbaren Ticker abrufen
    available_tickers = get_available_stocks()
    if not available_tickers:
        print("Keine Ticker verfügbar!")
        return

    # Hier kann eine beliebige Teilmenge der Ticker ausgewählt werden.
    # Zum Beispiel: tickers_to_test = ["AAPL", "MSFT", "GOOGL"]
    tickers_to_test = available_tickers  
    print(f"Vergleiche Strategien für die Ticker: {', '.join(tickers_to_test)}")

    # Zeitraum für den Backtest (anpassbar)
    start_date = "2010-01-01"
    end_date = "2020-12-31"

    # Ergebnis-Dictionary zur Speicherung der Performance jeder Strategie pro Ticker
    # Struktur: results[strategy_name] = {"totals": [..], "profits": [..]}
    results = {strategy_name: {"totals": [], "profits": []} for strategy_name in STRATEGIES.keys()}

    # Iteriere über alle ausgewählten Ticker
    for ticker in tickers_to_test:
        print(f"\nBearbeite Ticker: {ticker}")
        try:
            df = load_stock_data(ticker, start_date, end_date)
            df = ensure_close_column(df)
        except Exception as e:
            print(f"Fehler beim Laden der Daten für {ticker}: {e}")
            continue

        # Für jeden Ticker alle Strategien ausführen
        for strategy_name, run_strategy in STRATEGIES.items():
            try:
                # Annahme: Jede Strategie-Funktion liefert: (fig1, fig2, total, profit)
                fig1, fig2, total, profit = run_strategy(df, start_kapital=100000)
                results[strategy_name]["totals"].append(total)
                results[strategy_name]["profits"].append(profit)
                print(f"  {strategy_name}: Gesamtwert = {total:,.2f} €, Gewinn = {profit:,.2f} €")
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
            print(f"  {strategy_name}: Durchschnittlicher Gesamtwert = {metrics['avg_total']:,.2f} €, Durchschnittlicher Gewinn = {metrics['avg_profit']:,.2f} €")
        else:
            print(f"  {strategy_name}: Keine gültigen Ergebnisse.")

    # Ermitteln der besten Strategie basierend auf dem durchschnittlichen Gesamtwert
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

if __name__ == "__main__":
    main()

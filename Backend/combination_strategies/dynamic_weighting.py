import sys
import os
import sqlite3
import pandas as pd
import itertools

# Füge den übergeordneten Ordner zum Suchpfad hinzu, damit Module aus dem Projekt-Root gefunden werden
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from Datenbank.api import get_available_stocks, load_stock_data

# Importiere die echten Strategien aus dem Ordner "strategies" (diese liegen im Projekt-Root)
from strategies.moving_average import run_strategy as strat_ma
from strategies.momentum import run_strategy as strat_momentum
from strategies.bollinger_bands import run_strategy as strat_bollinger
from strategies.breakout_strategie import run_strategy as strat_breakout
from strategies.fibonacci import run_strategy as strat_fibonacci
from strategies.relative_strength import run_strategy as strat_rs
from strategies.buy_and_hold import run_strategy as strat_buyhold
from strategies.september_december import run_strategy as strat_septdec

STRATEGIES = {
    "Momentum": strat_momentum,
    "Moving Average": strat_ma,
    "Bollinger Bands": strat_bollinger,
    "Breakout Strategie": strat_breakout,
    "Fibonacci": strat_fibonacci,
    "Relative Strength": strat_rs,
    "Buy & Hold": strat_buyhold,
    "September/December": strat_septdec,
}

# Gemeinsame Hilfsfunktionen
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

def format_currency(value):
    """
    Formatiert einen Zahlenwert als Währung:
    Tausender werden mit einem Punkt getrennt und Dezimalstellen mit einem Komma.
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

def extract_numeric_result(result):
    """
    Extrahiert aus dem Rückgabewert der Strategie die numerischen Ergebnisse.
    Falls die Funktion 4 Werte zurückgibt (fig1, fig2, final_value, profit),
    werden nur final_value und profit extrahiert.
    Falls 2 Werte zurückgegeben werden, wird direkt das Tupel zurückgegeben.
    """
    if isinstance(result, tuple):
        if len(result) == 4:
            return result[2], result[3]
        elif len(result) == 2:
            return result
    raise ValueError("Unbekanntes Rückgabeformat der Strategie.")

def save_results(average_results, best_combo, best_metrics, output_path="results_dynamic_weighting.txt"):
    """
    Speichert die durchschnittlichen Ergebnisse und die beste Strategie-Kombination in eine Textdatei.
    Existierende Dateien werden gelöscht bzw. überschrieben.
    """
    if os.path.exists(output_path):
        os.remove(output_path)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("Durchschnittliche Performance pro Strategie-Kombination:\n")
        for combo, data in average_results.items():
            f.write(f"{combo[0]} + {combo[1]}: Durchschnittlicher Endwert = €{format_currency(data['avg_final'])}, "
                    f"Gewinn = €{format_currency(data['avg_profit'])}, Veränderung = {format_currency(data['avg_percent'])} %\n")
            f.write(f"    Durchschnittliche Gewichte: {combo[0]} = {data['avg_weights'][0]:.3f}, {combo[1]} = {data['avg_weights'][1]:.3f}\n")
        f.write("\nBeste Strategie-Kombination:\n")
        if best_combo:
            f.write(f"{best_combo[0]} + {best_combo[1]} mit einem durchschnittlichen Endwert von €{format_currency(best_metrics['avg_final'])} "
                    f"(Gewinn: €{format_currency(best_metrics['avg_profit'])}, {format_currency(best_metrics['avg_percent'])} %)\n")
            f.write(f"Durchschnittliche Gewichte: {best_combo[0]} = {best_metrics['avg_weights'][0]:.3f}, {best_combo[1]} = {best_metrics['avg_weights'][1]:.3f}\n")
        else:
            f.write("Keine Kombination konnte erfolgreich ausgewertet werden.\n")
    
    print(f"Ergebnisse wurden in '{output_path}' gespeichert.")

def main():
    # Alle verfügbaren Ticker aus der Datenbank abrufen
    available_tickers = get_available_stocks()
    if not available_tickers:
        print("Keine Ticker verfügbar!")
        return

    # Filtere nur Aktien (Stocks)
    tickers_to_test = filter_stocks(available_tickers)
    if not tickers_to_test:
        print("Nach Filterung sind keine Aktien (Stocks) verfügbar!")
        return
    print(f"Vergleiche kombinierte Strategien für die Ticker: {', '.join(tickers_to_test)}")

    # Zeitraum und Startkapital
    start_date = "2010-01-01"
    end_date = "2020-12-31"
    start_kapital = 100000

    # Erstelle alle paarweisen Kombinationen (ohne Wiederholung)
    strategy_names = list(STRATEGIES.keys())
    strategy_combinations = list(itertools.combinations(strategy_names, 2))

    # Ergebnis-Dictionary zur Speicherung der Performance jeder Kombination (über alle Ticker)
    combined_results = {combo: {"finals": [], "profits": [], "percents": [], "weights": []} for combo in strategy_combinations}

    # Für jeden Ticker (Daten werden aus der Datenbank geladen)
    for ticker in tickers_to_test:
        print(f"\nBearbeite Ticker: {ticker}")
        try:
            df = load_stock_data(ticker, start_date, end_date)
            df = ensure_close_column(df)
            df = ensure_datetime_index(df)
            # Falls vorhanden, setze die "date"-Spalte als Index und normalisiere
            if "date" in df.columns:
                df.set_index("date", inplace=True)
                df.index = df.index.normalize()
        except Exception as e:
            print(f"Fehler beim Laden der Daten für {ticker}: {e}")
            continue

        # Für jede Kombination: dynamisches Weighting
        for combo in strategy_combinations:
            strat1_name, strat2_name = combo
            try:
                # Jede Strategie wird auf das volle Startkapital simuliert (die Daten stammen aus der DB)
                res1 = STRATEGIES[strat1_name](df, start_kapital=start_kapital)
                res2 = STRATEGIES[strat2_name](df, start_kapital=start_kapital)
                final1, profit1 = extract_numeric_result(res1)
                final2, profit2 = extract_numeric_result(res2)

                # Berechne die Returns (Multiplikatoren)
                ret1 = final1 / start_kapital
                ret2 = final2 / start_kapital

                # Dynamische Gewichte basierend auf den Returns
                if (ret1 + ret2) == 0:
                    w1, w2 = 0.5, 0.5
                else:
                    w1 = ret1 / (ret1 + ret2)
                    w2 = ret2 / (ret1 + ret2)

                # Kombinierter Endwert über dynamisches Weighting
                combined_final = w1 * final1 + w2 * final2
                combined_profit = combined_final - start_kapital
                combined_percent = (combined_final - start_kapital) / start_kapital * 100

                combined_results[combo]["finals"].append(combined_final)
                combined_results[combo]["profits"].append(combined_profit)
                combined_results[combo]["percents"].append(combined_percent)
                combined_results[combo]["weights"].append((w1, w2))
                
                # Detaillierte Ausgabe zur Analyse
                print(f"  {strat1_name} + {strat2_name}:")
                print(f"    {strat1_name}: final = {final1:,.2f} ({ret1:.3f}x), {strat2_name}: final = {final2:,.2f} ({ret2:.3f}x)")
                print(f"    Gewichte: {strat1_name} = {w1:.3f}, {strat2_name} = {w2:.3f}")
                print(f"    Kombinierter Endwert = €{combined_final:,.2f}, Gewinn = €{combined_profit:,.2f}, Veränderung = {combined_percent:,.2f} %")
            except Exception as e:
                print(f"  Fehler bei der Kombination '{strat1_name} + {strat2_name}' für {ticker}: {e}")

    # Durchschnittliche Performance pro Kombination berechnen
    print("\nDurchschnittliche Performance pro Strategie-Kombination:")
    average_results = {}
    for combo, data in combined_results.items():
        if data["finals"]:
            avg_final = sum(data["finals"]) / len(data["finals"])
            avg_profit = sum(data["profits"]) / len(data["profits"])
            avg_percent = sum(data["percents"]) / len(data["percents"])
            avg_w1 = sum(w[0] for w in data["weights"]) / len(data["weights"])
            avg_w2 = sum(w[1] for w in data["weights"]) / len(data["weights"])
            average_results[combo] = {"avg_final": avg_final, "avg_profit": avg_profit, "avg_percent": avg_percent,
                                      "avg_weights": (avg_w1, avg_w2)}
            print(f"  {combo[0]} + {combo[1]}: Durchschnittlicher Endwert = €{format_currency(avg_final)}, "
                  f"Gewinn = €{format_currency(avg_profit)}, Veränderung = {format_currency(avg_percent)} %")
            print(f"    Durchschnittliche Gewichte: {combo[0]} = {avg_w1:.3f}, {combo[1]} = {avg_w2:.3f}")
        else:
            print(f"  {combo[0]} + {combo[1]}: Keine gültigen Ergebnisse.")

    # Beste Kombination ermitteln (basierend auf durchschnittlichem Endwert)
    best_combo = None
    best_avg_final = -float("inf")
    for combo, metrics in average_results.items():
        if metrics["avg_final"] > best_avg_final:
            best_avg_final = metrics["avg_final"]
            best_combo = combo

    print("\nBeste Strategie-Kombination (basierend auf durchschnittlichem Endwert):")
    if best_combo:
        best_metrics = average_results[best_combo]
        print(f"{best_combo[0]} + {best_combo[1]} mit einem durchschnittlichen Endwert von €{format_currency(best_metrics['avg_final'])} "
              f"(Gewinn: €{format_currency(best_metrics['avg_profit'])}, {format_currency(best_metrics['avg_percent'])} %)")
        print(f"Durchschnittliche Gewichte: {best_combo[0]} = {best_metrics['avg_weights'][0]:.3f}, {best_combo[1]} = {best_metrics['avg_weights'][1]:.3f}")
    else:
        print("Keine Kombination konnte erfolgreich ausgewertet werden.")

    # Ergebnisse in der Datei "results_dynamic_weighting.txt" speichern
    save_results(average_results, best_combo, average_results[best_combo] if best_combo in average_results else {}, output_path="results_dynamic_weighting.txt")

if __name__ == "__main__":
    main()

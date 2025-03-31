import sys
import os
import sqlite3
import pandas as pd
import itertools

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from Datenbank.api import get_available_stocks, load_stock_data
from strategies.common import ensure_close_column, ensure_datetime_index, filter_stocks, extract_numeric_result, format_currency

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


def save_results(average_results, best_combo, best_metrics, start_date, end_date, traded_stocks, output_path):
    results_lines = []
    results_lines.append(f"Handelszeitraum: {start_date} bis {end_date}\n")
    results_lines.append(f"Gehandelte Aktien: {', '.join(traded_stocks)}\n\n")
    results_lines.append("Ergebnisse pro Strategie-Kombination:\n")
    for combo, data in average_results.items():
        results_lines.append(
            f"{combo[0]} + {combo[1]}: Durchschnittlicher Endwert = €{format_currency(data['avg_final'])}, "
            f"Gewinn = €{format_currency(data['avg_profit'])}, Veränderung = {format_currency(data['avg_percent'])} %\n"
        )
        results_lines.append(
            f"Durchschnittliche Gewichte: {combo[0]} = {data['avg_weights'][0]:.3f}, {combo[1]} = {data['avg_weights'][1]:.3f}\n"
        )
    results_lines.append("\nBeste Strategie-Kombination:\n")
    if best_combo:
        results_lines.append(
            f"{best_combo[0]} + {best_combo[1]} mit einem durchschnittlichen Endwert von €{format_currency(best_metrics['avg_final'])} "
            f"(Gewinn: €{format_currency(best_metrics['avg_profit'])}, {format_currency(best_metrics['avg_percent'])} %)\n"
        )
        results_lines.append(
            f"Durchschnittliche Gewichte: {best_combo[0]} = {best_metrics['avg_weights'][0]:.3f}, {best_combo[1]} = {best_metrics['avg_weights'][1]:.3f}\n"
        )
    else:
        results_lines.append("Keine Kombination konnte erfolgreich ausgewertet werden.\n")
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(results_lines)
    
    print(f"Ergebnisse wurden in '{output_path}' gespeichert.")

def run_for_period(start_date, end_date, output_path):
    print(f"\n*** Starte Backtest für Zeitraum: {start_date} bis {end_date} ***")
    available_tickers = get_available_stocks()
    if not available_tickers:
        print("Keine Ticker verfügbar!")
        return

    tickers_to_test = filter_stocks(available_tickers)
    if not tickers_to_test:
        print("Nach Filterung sind keine Aktien (Stocks) verfügbar!")
        return
    print(f"Vergleiche kombinierte Strategien für die Ticker: {', '.join(tickers_to_test)}")

    start_kapital = 100000
    strategy_names = list(STRATEGIES.keys())
    strategy_combinations = list(itertools.combinations(strategy_names, 2))
    combined_results = {combo: {"finals": [], "profits": [], "percents": [], "weights": []} for combo in strategy_combinations}

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

        for combo in strategy_combinations:
            strat1_name, strat2_name = combo
            try:
                res1 = STRATEGIES[strat1_name](df, start_kapital=start_kapital)
                res2 = STRATEGIES[strat2_name](df, start_kapital=start_kapital)
                final1, profit1 = extract_numeric_result(res1)
                final2, profit2 = extract_numeric_result(res2)
                ret1 = final1 / start_kapital
                ret2 = final2 / start_kapital
                if (ret1 + ret2) == 0:
                    w1, w2 = 0.5, 0.5
                else:
                    w1 = ret1 / (ret1 + ret2)
                    w2 = ret2 / (ret1 + ret2)
                combined_final = w1 * final1 + w2 * final2
                combined_profit = combined_final - start_kapital
                combined_percent = (combined_final - start_kapital) / start_kapital * 100
                combined_results[combo]["finals"].append(combined_final)
                combined_results[combo]["profits"].append(combined_profit)
                combined_results[combo]["percents"].append(combined_percent)
                combined_results[combo]["weights"].append((w1, w2))
                print(f"{strat1_name} + {strat2_name}:")
                print(f"{strat1_name}: final = {final1:,.2f} ({ret1:.3f}x), {strat2_name}: final = {final2:,.2f} ({ret2:.3f}x)")
                print(f"Gewichte: {strat1_name} = {w1:.3f}, {strat2_name} = {w2:.3f}")
                print(f"Kombinierter Endwert = €{combined_final:,.2f}, Gewinn = €{combined_profit:,.2f}, Veränderung = {combined_percent:,.2f} %")
            except Exception as e:
                print(f"Fehler bei der Kombination '{strat1_name} + {strat2_name}' für {ticker}: {e}")

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
            print(f"Durchschnittliche Gewichte: {combo[0]} = {avg_w1:.3f}, {combo[1]} = {avg_w2:.3f}")
        else:
            print(f"{combo[0]} + {combo[1]}: Keine gültigen Ergebnisse.")

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
        best_metrics = {}

    save_results(average_results, best_combo, best_metrics, start_date, end_date, tickers_to_test, output_path)

def main():
    date_periods = {
        "2012_2023": ("2012-01-01", "2023-12-31"),
        "2012_2017": ("2012-01-01", "2017-12-31"),
        "2018_2023": ("2018-01-01", "2023-12-31")
    }

    for label, (start_date, end_date) in date_periods.items():
        output_file = f"results_dynamic_weighting_{label}.txt"
        run_for_period(start_date, end_date, output_file)

if __name__ == "__main__":
    main()


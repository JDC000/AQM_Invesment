#!/usr/bin/env python
import sys
import os
import sqlite3
import pandas as pd
import itertools
import numpy as np
import plotly.graph_objects as go

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from Datenbank.api import load_stock_data
from strategies.common import (
    ensure_close_column,
    ensure_datetime_index,
    extract_numeric_result,
    format_currency,
    calculate_vt_performance
)
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

TICKER = "VT"
START_DATE = "2010-01-01"
END_DATE = "2023-12-31"
START_CAPITAL = 100000

def run_single_strategies(df):
    results = {}
    for name, func in STRATEGIES.items():
        try:
            res = func(df, start_kapital=START_CAPITAL)
            final_value, profit = extract_numeric_result(res)
            percent_gain = (final_value - START_CAPITAL) / START_CAPITAL * 100
            results[name] = {
                "final_value": final_value,
                "profit": profit,
                "percent": percent_gain
            }
        except Exception as e:
            results[name] = {"error": str(e)}
    return results


def main():
    df = load_stock_data(TICKER, START_DATE, END_DATE)
    if df is None or df.empty:
        print(f"Keine Daten für {TICKER} gefunden.")
        return
    df = ensure_close_column(df)
    df = ensure_datetime_index(df)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)
        df.index = df.index.normalize()

    single_results = run_single_strategies(df)
    vt_performance = calculate_vt_performance(df,START_CAPITAL)
    output_file = "results_VT.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"Ergebnisse für {TICKER}\n")
        f.write(f"Handelszeitraum: {START_DATE} bis {END_DATE}\n")
        f.write(f"Startkapital: €{format_currency(START_CAPITAL)}\n\n")
        
        f.write("=== Einzelstrategien ===\n")
        for name, data in single_results.items():
            if "error" in data:
                f.write(f"{name}: Fehler: {data['error']}\n")
            else:
                f.write(f"{name}: Endwert = €{format_currency(data['final_value'])}, "
                        f"Gewinn = €{format_currency(data['profit'])}, "
                        f"Prozentuale Veränderung = {format_currency(data['percent'])} %\n")
        
        f.write("\n=== VT Performance (Buy & Hold) ===\n")
        f.write(f"VT: Endwert = €{format_currency(vt_performance['final_value'])}, "
                f"Gewinn = €{format_currency(vt_performance['profit'])}, "
                f"Prozentuale Veränderung = {format_currency(vt_performance['percent'])} %\n")
    
    print(f"Alle Ergebnisse wurden in '{output_file}' gespeichert.")


if __name__ == "__main__":
    main()

import sys
import os
import pandas as pd
import numpy as np

# Füge den übergeordneten Ordner zum Suchpfad hinzu
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from Datenbank.api import get_available_stocks, load_stock_data

# Importiere die Strategien ohne zusätzlichen Parameter (start_capital wird intern angenommen)
from strategies.momentum import run_strategy as strat_momentum
from strategies.breakout_strategie import run_strategy as strat_breakout
from strategies.bollinger_bands import run_strategy as strat_bollinger
from strategies.relative_strength import run_strategy as strat_rs

# ------------------------------
# Gemeinsame Hilfsfunktionen
# ------------------------------
def ensure_close_column(df):
    if "close" not in df.columns:
        if "Price" in df.columns:
            df = df.rename(columns={"Price": "close"})
        else:
            raise ValueError("Das DataFrame enthält weder 'close' noch 'Price'")
    return df

def ensure_datetime_index(df):
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
    return df

def filter_stocks(tickers):
    ETFS = {"XFI", "XIT", "XLB", "XLE", "XLF", "XLI", "XLP", "XLU", "XLV", "XLY", "XSE", "VT"}
    CRYPTOS = {"BNB", "XRP", "SOL", "DOT", "LTC", "USDC", "LINK", "BCH", "XLM", "UNI",
               "ATOM", "TRX", "ETC", "NEAR", "XMR", "VET", "EOS", "FIL", "CRO", "DAI", "DASH", "ENJ"}
    return [ticker for ticker in tickers if ticker not in ETFS and ticker not in CRYPTOS]

def extract_numeric_result(result):
    """
    Extrahiert aus dem Rückgabewert der Strategie den finalen Kapitalwert und den Gewinn.
    Unterstützt Rückgabeformate mit 2 oder 4 Werten.
    """
    if isinstance(result, tuple):
        if len(result) == 4:
            return result[2], result[3]
        elif len(result) == 2:
            return result
    raise ValueError("Unbekanntes Rückgabeformat der Strategie.")

# ------------------------------
# Dynamische Marktphasen-Erkennung und Segmentierung
# ------------------------------
def add_regime_signal(df):
    """
    Berechnet täglich SMA20 und SMA50 und bestimmt das Regime.
    Liefert eine neue Spalte 'regime', die ab dem 50. Tag gültig ist.
    """
    df['SMA20'] = df['close'].rolling(window=20).mean()
    df['SMA50'] = df['close'].rolling(window=50).mean()
    
    regimes = [None] * len(df)
    for i in range(len(df)):
        if i < 49:  # nicht genügend Daten für SMA50
            regimes[i] = None
        else:
            current = df.iloc[i]
            sma_diff = abs(current['SMA20'] - current['SMA50'])
            threshold = 0.005 * current['close']  # z. B. 0,5 % des aktuellen Preises
            if sma_diff < threshold:
                regimes[i] = "sideways"
            elif current['SMA20'] > current['SMA50']:
                regimes[i] = "bullish"
            else:
                regimes[i] = "bearish"
    df['regime'] = regimes
    return df

def identify_segments(df):
    """
    Identifiziert zusammenhängende Segmente mit gleichem Regime (Überspringen von None).
    Liefert eine Liste von Tupeln: (Regime, Startdatum, Enddatum)
    """
    segments = []
    current_regime = None
    current_start = None
    for date, row in df.iterrows():
        regime = row['regime']
        if regime is None:
            continue
        if current_regime is None:
            current_regime = regime
            current_start = date
        elif regime != current_regime:
            segments.append((current_regime, current_start, date))
            current_regime = regime
            current_start = date
    if current_regime is not None and current_start is not None:
        segments.append((current_regime, current_start, df.index[-1]))
    return segments

# ------------------------------
# Dynamischer Backtest über Segmente
# ------------------------------
def dynamic_regime_backtest(df, start_capital=100000):
    """
    Führt einen dynamischen Backtest durch, bei dem das Regime täglich ermittelt
    und in Segmenten die jeweilige Strategie angewendet wird. Die prozentuale Veränderung
    jedes Segments wird auf das Gesamtportfolio angewandt.
    """
    df = ensure_close_column(df)
    df = ensure_datetime_index(df)
    df = df.sort_index()
    
    df = add_regime_signal(df)
    segments = identify_segments(df)
    
    portfolio_value = start_capital
    segment_returns = []  # Zur Aggregation der Renditen
    
    for regime, seg_start, seg_end in segments:
        segment_data = df.loc[seg_start:seg_end]
        try:
            if regime in ["bullish", "bearish"]:
                final_mom, _ = extract_numeric_result(strat_momentum(segment_data))
                final_break, _ = extract_numeric_result(strat_breakout(segment_data))
                if final_mom >= final_break:
                    seg_final = final_mom
                else:
                    seg_final = final_break
            elif regime == "sideways":
                final_boll, _ = extract_numeric_result(strat_bollinger(segment_data))
                final_rs, _ = extract_numeric_result(strat_rs(segment_data))
                seg_final = (final_boll + final_rs) / 2
            else:
                seg_final = start_capital
            segment_return = (seg_final - start_capital) / start_capital
            segment_returns.append(segment_return)
            portfolio_value *= (1 + segment_return)
        except Exception as e:
            # Falls ein Fehler auftritt, wird das Segment ignoriert
            continue
    return portfolio_value, segment_returns

# ------------------------------
# Backtest über einen Zeitraum für einen Ticker
# ------------------------------
def run_dynamic_for_ticker(ticker, start_date, end_date):
    output_lines = []
    output_lines.append(f"Ticker: {ticker}\n")
    try:
        df = load_stock_data(ticker, start_date, end_date)
        df = ensure_close_column(df)
        df = ensure_datetime_index(df)
        if "date" in df.columns:
            df.set_index("date", inplace=True)
            df.index = pd.to_datetime(df.index).normalize()
    except Exception as e:
        output_lines.append(f"Fehler beim Laden der Daten für {ticker}: {e}\n")
        return None, output_lines

    final_value, segment_returns = dynamic_regime_backtest(df)
    overall_return = (final_value - 100000) / 100000 * 100
    output_lines.append(f"Endgültiger Portfolio-Wert: €{final_value:,.2f} (Return: {overall_return:.2f} %)\n\n")
    return final_value, output_lines

# ------------------------------
# Main-Funktion: Ergebnisse in Textdateien speichern (Zusammenfassung pro Zeitraum)
# ------------------------------
def main():
    # Definiere Zeiträume und zugehörige Output-Dateinamen
    date_periods = {
        "2012_2023": ("2012-01-01", "2023-12-31"),
        "2012_2017": ("2012-01-01", "2017-12-31"),
        "2018_2023": ("2018-01-01", "2023-12-31")
    }
    
    available_tickers = get_available_stocks()
    tickers_to_test = filter_stocks(available_tickers)
    
    for label, (start_date, end_date) in date_periods.items():
        output_file = f"results_marktphasenansatz_{label}.txt"
        all_output = []
        all_output.append(f"*** Backtest Zeitraum: {start_date} bis {end_date} ***\n\n")
        
        ticker_results = []  # Zum Aggregieren der Endwerte für den Zeitraum
        
        for ticker in tickers_to_test:
            final_value, ticker_output = run_dynamic_for_ticker(ticker, start_date, end_date)
            if final_value is not None:
                ticker_results.append((ticker, final_value))
            all_output.extend(ticker_output)
        
        # Berechne zusammenfassende Kennzahlen für diesen Zeitraum
        if ticker_results:
            values = [res[1] for res in ticker_results]
            avg_value = np.mean(values)
            best_ticker, best_value = max(ticker_results, key=lambda x: x[1])
            worst_ticker, worst_value = min(ticker_results, key=lambda x: x[1])
            summary = (
                "\n*** Zusammenfassung ***\n"
                f"Anzahl ausgewerteter Ticker: {len(ticker_results)}\n"
                f"Durchschnittlicher Endwert: €{avg_value:,.2f}\n"
                f"Bestes Ergebnis: {best_ticker} mit €{best_value:,.2f}\n"
                f"Schlechtestes Ergebnis: {worst_ticker} mit €{worst_value:,.2f}\n"
            )
            all_output.append(summary)
        else:
            all_output.append("Keine gültigen Ergebnisse für diesen Zeitraum.\n")
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.writelines(all_output)
        print(f"\nErgebnisse für Zeitraum {label} wurden in '{output_file}' gespeichert.")

if __name__ == "__main__":
    main()

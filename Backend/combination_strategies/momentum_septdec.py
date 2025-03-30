import sys
import os
import sqlite3
import pandas as pd

# Füge den übergeordneten Ordner zum Suchpfad hinzu, damit Module aus dem Projekt-Root gefunden werden
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from Datenbank.api import get_available_stocks, load_stock_data

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

def save_results(average_final, average_profit, average_percent, start_date, end_date, traded_stocks, output_path):
    """
    Speichert die durchschnittlichen Ergebnisse, den Handelszeitraum und die gehandelten Aktien in eine Textdatei.
    Existierende Dateien werden überschrieben.
    """
    results_lines = []
    results_lines.append(f"Handelszeitraum: {start_date} bis {end_date}\n")
    results_lines.append(f"Gehandelte Aktien: {', '.join(traded_stocks)}\n\n")
    results_lines.append("Durchschnittliche Performance:\n")
    results_lines.append(f"  Durchschnittlicher Endwert = €{format_currency(average_final)}\n")
    results_lines.append(f"  Durchschnittlicher Gewinn = €{format_currency(average_profit)}\n")
    results_lines.append(f"  Durchschnittliche Veränderung = {format_currency(average_percent)} %\n")
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(results_lines)
    
    print(f"Ergebnisse wurden in '{output_path}' gespeichert.")

def run_for_period(start_date, end_date, output_path):
    """
    Führt den Backtest für den angegebenen Zeitraum über alle gefilterten Aktien durch.
    Für jedes Jahr wird vor dem Einstieg in den September geprüft, ob das 3-Monats-Momentum positiv ist.
    Ist dies der Fall, wird am ersten September-Tag gekauft und am ersten Dezember-Tag verkauft.
    Andernfalls bleibt das Kapital unberührt.
    """
    print(f"\n*** Starte Backtest für Zeitraum: {start_date} bis {end_date} ***")
    available_tickers = get_available_stocks()
    if not available_tickers:
        print("Keine Ticker verfügbar!")
        return
    tickers_to_test = filter_stocks(available_tickers)
    if not tickers_to_test:
        print("Nach Filterung sind keine Aktien (Stocks) verfügbar!")
        return
    print(f"Teste Strategie für die Ticker: {', '.join(tickers_to_test)}")
    
    start_kapital = 100000
    results = {}
    
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
        
        # Setze standardmäßig Signal-Spalte auf 0
        df['signal'] = 0
        
        # Iteriere über jedes Jahr und prüfe, ob für das jeweilige Jahr ein positiver 3-Monats-Momentum
        # vor dem 1. September vorliegt.
        years = df.index.year.unique()
        for year in years:
            sep_mask = (df.index.year == year) & (df.index.month == 9)
            dec_mask = (df.index.year == year) & (df.index.month == 12)
            if sep_mask.any() and dec_mask.any():
                sep_day = df[sep_mask].index.min()
                dec_day = df[dec_mask].index.min()
                three_months_ago = sep_day - pd.DateOffset(months=3)
                df_before = df[df.index <= three_months_ago]
                if df_before.empty:
                    continue  # nicht genügend Daten
                price_before = df_before.iloc[-1]['close']
                price_sep = df.loc[sep_day, 'close']
                momentum_val = (price_sep - price_before) / price_before
                if momentum_val > 0:
                    # Bei positivem 3-Monats-Momentum: volles Investment in September/December
                    df.loc[sep_day, 'signal'] = 1
                    df.loc[dec_day, 'signal'] = -1
        
        # Simuliere die Trades
        kapital = start_kapital
        position = 0
        equity_curve = []
        for i in range(len(df)):
            preis = df.iloc[i]['close']
            signal = df.iloc[i]['signal']
            if signal == 1 and position == 0:
                # Kaufe mit 100% des Kapitals
                position = kapital / preis
                kapital = 0
            elif signal == -1 and position > 0:
                # Verkauf
                kapital = position * preis
                position = 0
            equity_curve.append(kapital + position * preis)
        final_value = equity_curve[-1] if equity_curve else start_kapital
        profit = final_value - start_kapital
        percent_change = (final_value - start_kapital) / start_kapital * 100
        
        results[ticker] = {"final_value": final_value, "profit": profit, "percent": percent_change}
        print(f"  Endwert = €{format_currency(final_value)}, Gewinn = €{format_currency(profit)}, Veränderung = {format_currency(percent_change)} %")
    
    if results:
        avg_final = sum(r["final_value"] for r in results.values()) / len(results)
        avg_profit = sum(r["profit"] for r in results.values()) / len(results)
        avg_percent = sum(r["percent"] for r in results.values()) / len(results)
        print("\nDurchschnittliche Performance über alle Ticker:")
        print(f"  Durchschnittlicher Endwert = €{format_currency(avg_final)}")
        print(f"  Durchschnittlicher Gewinn = €{format_currency(avg_profit)}")
        print(f"  Durchschnittliche Veränderung = {format_currency(avg_percent)} %")
    else:
        print("Keine gültigen Ergebnisse.")
        avg_final = avg_profit = avg_percent = 0

    save_results(avg_final, avg_profit, avg_percent, start_date, end_date, tickers_to_test, output_path)

def main():
    # Definiere die gewünschten Zeiträume und zugehörigen Output-Dateinamen
    date_periods = {
        "2012_2023": ("2012-01-01", "2023-12-31"),
        "2012_2017": ("2012-01-01", "2017-12-31"),
        "2018_2023": ("2018-01-01", "2023-12-31")
    }
    for label, (start_date, end_date) in date_periods.items():
        output_file = f"results_momentum_september_december_{label}.txt"
        run_for_period(start_date, end_date, output_file)

if __name__ == "__main__":
    main()

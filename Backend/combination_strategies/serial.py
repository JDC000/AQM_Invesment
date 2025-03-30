import os
import sys
import sqlite3
import pandas as pd


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
      ETFS = {"XFI", "XIT", "XLB", "XLE", "XLF", "XLI", "XLP", "XLU", "XLV", "XLY", "XSE", "VT"}
      CRYPTOS = {"BNB", "XRP", "SOL", "DOT", "LTC", "USDC", "LINK", "BCH", "XLM", "UNI",
                 "ATOM", "TRX", "ETC", "NEAR", "XMR", "VET", "EOS", "FIL", "CRO", "DAI", "DASH", "ENJ"}
    """
    ETFS = {"XFI", "XIT", "XLB", "XLE", "XLF", "XLI", "XLP", "XLU", "XLV", "XLY", "XSE", "VT"}
    CRYPTOS = {"BNB", "XRP", "SOL", "DOT", "LTC",
               "USDC", "LINK", "BCH", "XLM", "UNI", "ATOM", "TRX",
               "ETC", "NEAR", "XMR", "VET", "EOS", "FIL", "CRO", "DAI", "DASH", "ENJ"}
    return [ticker for ticker in tickers if ticker not in ETFS and ticker not in CRYPTOS]


def format_currency(value):
    """
    Formatiert einen Zahlenwert als Währung:
    Tausender werden mit einem Punkt getrennt und die Nachkommastellen mit einem Komma.
    Beispiel: 100000 -> "100.000,00"
    """
    s = f"{value:,.2f}"  # Beispiel: 100,000.00 (englisches Format)
    # Tauschen: Komma -> Temporärmarke, Punkt -> Komma, Temporärmarke -> Punkt
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return s


def save_strategy_results(results, traded_stocks, start_date, end_date, output_path="results_strategy_serial.txt"):
    """
    Speichert die Ergebnisse der Strategie für alle Aktien in eine Textdatei.
    Existierende Dateien werden überschrieben.
    Am Anfang werden der Handelszeitraum und die gehandelten Aktien ausgegeben.
    Anschließend folgen die Ergebnisse pro Aktie und am Ende die Durchschnittswerte.
    """
    if os.path.exists(output_path):
        os.remove(output_path)
    
    with open(output_path, "w", encoding="utf-8") as f:
        # Kopfzeile mit Handelszeitraum und gehandelten Aktien
        f.write("Ergebnisse der Serial-Strategie für alle Aktien\n")
        f.write("Handelszeitraum: " + start_date + " bis " + end_date + "\n")
        f.write("Gehandelte Aktien: " + ", ".join(traded_stocks) + "\n\n")
        
        for r in results:
            f.write(f"Symbol: {r['symbol']}\n")
            f.write("Startwert: €" + format_currency(r['start_value']) + "\n")
            f.write("Endwert: €" + format_currency(r['final_value']) + "\n")
            f.write("Gewinn/Verlust: €" + format_currency(r['gewinn']) + "\n")
            f.write("Prozentuale Veränderung: " + format_currency(r['percent_change']) + " %\n")
            f.write("\n")
        
        # Berechne Durchschnittswerte
        if results:
            avg_final_value = sum(x["final_value"] for x in results) / len(results)
            avg_gewinn = sum(x["gewinn"] for x in results) / len(results)
            avg_percent_change = sum(x["percent_change"] for x in results) / len(results)
            f.write("Durchschnittswerte:\n")
            f.write("Durchschnittlicher Endwert: €" + format_currency(avg_final_value) + "\n")
            f.write("Durchschnittlicher Gewinn/Verlust: €" + format_currency(avg_gewinn) + "\n")
            f.write("Durchschnittliche Prozentuale Veränderung: " + format_currency(avg_percent_change) + " %\n")
    
    print(f"Alle Ergebnisse wurden in '{output_path}' gespeichert.")


def run_strategy_serial(df, start_kapital):
    """
    Ein Beispiel für eine einfache Buy-&-Hold-Strategie:
    - Es wird der Startpreis (erster 'close'-Wert) und der Endpreis (letzter 'close'-Wert) ermittelt.
    - Der Endkapitalwert und der Gewinn werden berechnet.
    - Es werden keine Diagramme erstellt (fig1 und fig2 sind None).
    """
    start_price = df.iloc[0]["close"]
    end_price = df.iloc[-1]["close"]
    final_value = start_kapital * (end_price / start_price)
    gewinn = final_value - start_kapital
    # Platzhalter für Diagramme (können später durch tatsächliche Plot-Erzeugung ersetzt werden)
    fig1 = None
    fig2 = None
    return fig1, fig2, final_value, gewinn


if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    BASE_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
    DB_NAME = os.path.join(BASE_DIR, "Datenbank", "DB", "investment.db")
    
    start_date = "2010-01-01"
    end_date = "2020-12-31"
    start_value = 100000
    
    # Verbindung zur Datenbank herstellen und alle existierenden Symbole abfragen
    try:
        conn = sqlite3.connect(DB_NAME)
        query_symbols = "SELECT DISTINCT symbol FROM market_data"
        df_symbols = pd.read_sql_query(query_symbols, conn)
        tickers = df_symbols["symbol"].tolist()
    except Exception as e:
        print("Fehler beim Laden der Symbole aus der Datenbank:", e)
        sys.exit(1)
    finally:
        conn.close()
    
    # Nur Aktien (keine ETFs, keine Cryptos) berücksichtigen
    filtered_tickers = filter_stocks(tickers)
    print("Verarbeitete Aktien:", filtered_tickers)
    
    results = []
    
    # Für jedes Symbol werden die entsprechenden Daten geladen, vorbereitet und die Serial-Strategie ausgeführt.
    for symbol in filtered_tickers:
        try:
            conn = sqlite3.connect(DB_NAME)
            query = """
                SELECT date, close
                FROM market_data
                WHERE symbol = ? AND date BETWEEN ? AND ?
                ORDER BY date
            """
            params = [symbol, start_date, end_date]
            df_stock = pd.read_sql_query(query, conn, params=params, parse_dates=["date"])
        except Exception as e:
            print(f"Fehler beim Laden der Daten für {symbol}:", e)
            continue
        finally:
            conn.close()
        
        try:
            df_stock = ensure_close_column(df_stock)
            df_stock = ensure_datetime_index(df_stock)
        except Exception as e:
            print(f"Fehler bei der Datenaufbereitung für {symbol}:", e)
            continue
        
        # Ausführung der Serial-Strategie
        try:
            fig1, fig2, final_value, gewinn = run_strategy_serial(df_stock, start_kapital=start_value)
        except Exception as e:
            print(f"Fehler bei der Ausführung der Serial-Strategie für {symbol}:", e)
            continue
        
        percent_change = (final_value - start_value) / start_value * 100
        results.append({
            "symbol": symbol,
            "start_value": start_value,
            "final_value": final_value,
            "gewinn": gewinn,
            "percent_change": percent_change
        })
        
        print(f"{symbol}: Endwert: €{format_currency(final_value)}, Gewinn: €{format_currency(gewinn)}, Veränderung: {format_currency(percent_change)} %")
        # Optional: Du könntest die Figuren speichern oder anzeigen, wenn gewünscht.
        # fig1.show()
        # fig2.show()
    
    # Durchschnittswerte berechnen und in der Konsole ausgeben
    if results:
        avg_final_value = sum(x["final_value"] for x in results) / len(results)
        avg_gewinn = sum(x["gewinn"] for x in results) / len(results)
        avg_percent_change = sum(x["percent_change"] for x in results) / len(results)
        print("\nDurchschnittswerte:")
        print("Durchschnittlicher Endwert: €" + format_currency(avg_final_value))
        print("Durchschnittlicher Gewinn/Verlust: €" + format_currency(avg_gewinn))
        print("Durchschnittliche Prozentuale Veränderung: " + format_currency(avg_percent_change) + " %")
    
    # Ergebnisse für alle verarbeiteten Aktien in einer Textdatei speichern
    save_strategy_results(results, filtered_tickers, start_date, end_date)

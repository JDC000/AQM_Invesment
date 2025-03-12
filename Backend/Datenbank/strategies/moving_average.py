import sqlite3
import pandas as pd
import numpy as np

# Datenbankpfad
DB_NAME = "backend/db/investment.db"

def get_stock_data(symbol):
    """Holt historische Aktienkurse aus der Datenbank"""
    conn = sqlite3.connect(DB_NAME)
    query = f"SELECT date, close FROM market_data WHERE symbol = '{symbol}' ORDER BY date ASC"
    df = pd.read_sql_query(query, conn)
    conn.close()
    df['date'] = pd.to_datetime(df['date'])  # Datumskonvertierung
    df.set_index('date', inplace=True)
    return df

def calculate_moving_average(df, short_window=50, long_window=200):
    """Berechnet den gleitenden Durchschnitt und Handelssignale"""
    df['SMA_short'] = df['close'].rolling(window=short_window).mean()
    df['SMA_long'] = df['close'].rolling(window=long_window).mean()

    # Handelssignale generieren
    df['signal'] = np.where(df['SMA_short'] > df['SMA_long'], 1, 0)  # 1 = Kaufen, 0 = Verkaufen
    df['crossover'] = df['signal'].diff()  # 1 = Kaufsignal, -1 = Verkaufssignal

    return df

def get_moving_average_strategy(symbol):
    """Wendet die Moving Average Strategie auf eine Aktie an"""
    df = get_stock_data(symbol)
    df = calculate_moving_average(df)
    
    # Nur die letzten 100 Einträge zurückgeben
    return df.tail(100).to_dict(orient='records')

if __name__ == "__main__":
    symbol = "AAPL"  # Test mit Apple
    result = get_moving_average_strategy(symbol)
    print(result)  # Ausgabe der Ergebnisse

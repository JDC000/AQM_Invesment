import sqlite3
import pandas as pd
import numpy as np

# Pfad zur SQLite-Datenbank
DB_NAME = "backend/db/investment.db"

def get_stock_data(symbol):
    """Lädt historische Daten einer Aktie aus der Datenbank"""
    conn = sqlite3.connect(DB_NAME)
    query = f"SELECT date, close FROM market_data WHERE symbol = '{symbol}' ORDER BY date ASC"
    df = pd.read_sql_query(query, conn)
    conn.close()
    df['date'] = pd.to_datetime(df['date'])  # Konvertiere Datum in DateTime-Format
    df.set_index('date', inplace=True)
    return df

def calculate_momentum(df, window=10):
    """Berechnet das Momentum anhand der prozentualen Preisänderung über ein bestimmtes Zeitfenster"""
    df['momentum'] = df['close'].pct_change(periods=window) * 100  # % Preisänderung
    df['signal'] = np.where(df['momentum'] > 5, 'KAUFEN', np.where(df['momentum'] < -5, 'VERKAUFEN', 'HALTEN'))
    return df

def get_momentum_strategy(symbol):
    """Berechnet die Momentum-Strategie für eine Aktie"""
    df = get_stock_data(symbol)
    df = calculate_momentum(df)
    return df.tail(50).to_dict(orient='records')  # Gibt die letzten 50 Tage zurück

if __name__ == "__main__":
    symbol = "AAPL"  # Test mit Apple-Aktie
    result = get_momentum_strategy(symbol)
    print(result)  # Ausgabe der Daten

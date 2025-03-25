import sqlite3
import os

# Pfad zur Datenbank (angepasst an deinen Speicherort)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = "/Users/hendrik_liebscher/Desktop/Git/AQM_Invesment/Backend/Datenbank/DB/investment.db"

# Zeitraum definieren
start_date = "2010-01-01"
end_date = "2020-12-31"

# Mindestanzahl an Einträgen, die als "genügend" gelten sollen
min_entries = 200

# Verbindung zur Datenbank herstellen
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# SQL-Abfrage: Anzahl der Einträge pro Symbol im definierten Zeitraum ermitteln
query = """
SELECT symbol, COUNT(*) AS entry_count
FROM market_data
WHERE date BETWEEN ? AND ?
GROUP BY symbol;
"""

cursor.execute(query, (start_date, end_date))
results = cursor.fetchall()

# Ergebnisse auswerten
for symbol, count in results:
    if count >= min_entries:
        print(f"{symbol} hat genügend Einträge ({count}) zwischen {start_date} und {end_date}.")
    else:
        print(f"{symbol} hat nicht genügend Einträge ({count}) zwischen {start_date} und {end_date}.")

conn.close()

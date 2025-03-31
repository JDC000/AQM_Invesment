import sqlite3
import os

DB_PATH = "/Users/hendrik_liebscher/Desktop/Git/AQM_Invesment/Backend/Datenbank/DB/investment.db"

start_date = "2010-01-01"
end_date = "2023-12-31"

# Mindestanzahl an Einträgen, die als ausreichend gelten 
min_entries = 200

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

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

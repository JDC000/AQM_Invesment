import sqlite3

# Name der Datenbank
DB_NAME = "investment.db"

def create_database():
    """Erstellt die SQLite-Datenbank und die Tabelle market_data"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Erstellen der Tabelle market_data für Aktien, ETFs und Kryptowährungen
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS market_data (
            asset_type TEXT,      -- Asset-Typ (Stock/ETF oder Crypto)
            symbol TEXT,          -- Aktien- oder Kryptowährungs-Ticker
            date TEXT,            -- Handelsdatum
            open REAL,            -- Eröffnungskurs
            high REAL,            -- Höchstkurs
            low REAL,             -- Tiefstkurs
            close REAL,           -- Schlusskurs
            volume REAL,          -- Handelsvolumen
            PRIMARY KEY (asset_type, symbol, date)
        )
    """)

    conn.commit()
    conn.close()
    print("Die Datenbank 'investment.db' wurde erfolgreich erstellt!")

# Datenbank erstellen
if __name__ == "__main__":
    create_database()

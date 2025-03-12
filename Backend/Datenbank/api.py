from flask import Flask, jsonify
from flask_cors import CORS
import sqlite3
import pandas as pd
from strategies.moving_average import get_moving_average_strategy
from strategies.momentum import get_momentum_strategy

# Flask-App initialisieren
app = Flask(__name__)
CORS(app)  # Erlaubt API-Aufrufe von externen Anwendungen

# Datenbankpfad
DB_NAME = "backend/db/investment.db"

def get_stock_data(symbol):
    """Holt historische Aktien- oder Krypto-Daten aus der SQLite-Datenbank"""
    conn = sqlite3.connect(DB_NAME)
    query = f"SELECT date, close FROM market_data WHERE symbol = '{symbol}' ORDER BY date ASC"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df.to_dict(orient="records")

@app.route("/")
def home():
    return jsonify({"message": "API ist aktiv! Verwenden Sie /api/stock/AAPL oder /api/strategy/moving_average/AAPL für Daten."})

@app.route("/api/stock/<symbol>")
def stock_data(symbol):
    """API-Endpunkt zum Abrufen historischer Aktienkurse"""
    data = get_stock_data(symbol)
    return jsonify(data)

@app.route("/api/strategy/moving_average/<symbol>")
def moving_average_strategy(symbol):
    """API-Endpunkt für die Moving Average Strategie"""
    data = get_moving_average_strategy(symbol)
    return jsonify(data)

@app.route("/api/strategy/momentum/<symbol>")
def momentum_strategy(symbol):
    """API-Endpunkt für die Momentum Strategie"""
    data = get_momentum_strategy(symbol)
    return jsonify(data)

if __name__ == "__main__":
    app.run(debug=True, port=5000)

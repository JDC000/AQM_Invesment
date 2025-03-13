from flask import Flask, jsonify, request
import sqlite3
import pandas as pd

app = Flask(__name__)

@app.route("/get_data", methods=["GET"])
def get_data():
    symbol = request.args.get("symbol", "").upper()
    if not symbol:
        return jsonify({"error": "Symbol is required"}), 400

    conn = sqlite3.connect("backend/db/investment.db")
    query = f"SELECT * FROM market_data WHERE symbol = '{symbol}'"
    df = pd.read_sql_query(query, conn)
    conn.close()

    return jsonify(df.to_dict(orient="records"))

if __name__ == "__main__":
    app.run(debug=True)

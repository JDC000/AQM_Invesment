import sqlite3
import pandas as pd
import dash
from dash import dcc, html
import plotly.express as px
from flask import Flask

# Erstelle eine Flask-App
server = Flask(__name__)
app = dash.Dash(__name__, server=server, suppress_callback_exceptions=True)

# Pfad zur SQLite-Datenbank
DB_NAME = "backend/db/investment.db"

def get_momentum_data(symbol):
    """Holt Momentum-Daten aus der Datenbank"""
    conn = sqlite3.connect(DB_NAME)
    query = f"SELECT date, close FROM market_data WHERE symbol = '{symbol}' ORDER BY date ASC"
    df = pd.read_sql_query(query, conn)
    conn.close()

    # Berechnung des Momentums (% Preisänderung der letzten 10 Tage)
    df["date"] = pd.to_datetime(df["date"])
    df["momentum"] = df["close"].pct_change(periods=10) * 100  # % Preisänderung
    return df

# Hole Daten für AAPL (Apple)
df = get_momentum_data("AAPL")

# Dash-Layout erstellen
app.layout = html.Div([
    html.H1("Momentum-Strategie - Dash & Plotly"),
    dcc.Dropdown(
        id="stock-dropdown",
        options=[
            {"label": "Apple (AAPL)", "value": "AAPL"},
            {"label": "Tesla (TSLA)", "value": "TSLA"},
            {"label": "Bitcoin (BTC)", "value": "BTC"}
        ],
        value="AAPL"
    ),
    dcc.Graph(id="momentum-graph"),
])

# Callback-Funktion zum Aktualisieren des Diagramms je nach gewählter Aktie
@app.callback(
    dash.dependencies.Output("momentum-graph", "figure"),
    [dash.dependencies.Input("stock-dropdown", "value")]
)
def update_graph(symbol):
    df = get_momentum_data(symbol)
    fig = px.line(df, x="date", y="momentum", title=f"Momentum für {symbol}")
    return fig

# App starten
if __name__ == "__main__":
    app.run_server(debug=True)

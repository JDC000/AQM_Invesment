import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import requests
from flask import Flask
import sqlite3

# Flask-Server für Dash
server = Flask(__name__)
app = dash.Dash(__name__, server=server, external_stylesheets=[dbc.themes.BOOTSTRAP])

# API-URL
API_BASE_URL = "http://127.0.0.1:5000/api"


def get_all_symbols():
    """Holt alle einzigartigen Symbole (Aktien, ETFs, Kryptos) aus der Datenbank"""
    conn = sqlite3.connect("/Users/jennycao/AQM_Invesment/Backend/Datenbank/DB/investment.db")
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT symbol FROM market_data")
    symbols = cursor.fetchall()
    conn.close()
    
    # Umwandeln in ein Format für Dash-Dropdown
    return [{"label": symbol[0], "value": symbol[0]} for symbol in symbols]


# Layout des Dashboards
app.layout = dbc.Container([
    html.H1("Investment Dashboard", className="text-center mb-4"),

    dbc.Row([
        dbc.Col([
            html.Label("Wählen Sie eine Strategie aus:"),
            dcc.Dropdown(
                id="strategy-dropdown",
                options=[
                    {"label": "Moving Average Crossover", "value": "moving_average"},
                    {"label": "Momentum Strategy", "value": "momentum"},
                    {"label": "Bollinger Bands", "value": "bollinger"},
                ],
                value="moving_average"
            ),
        ], width=6),
        dbc.Col([
            html.Label("Wählen Sie ein Finanzinstrument aus:"),
            dcc.Dropdown(
                id="stock-dropdown",
                options=get_all_symbols(),  # Dynamisch alle verfügbaren Symbole abrufen
                value="AAPL"
            ),
        ], width=6),
    ], className="mb-4"),

    dbc.Row([
        dbc.Col([
            html.H4("Aktueller Kurs"),
            dcc.Graph(id="stock-price-graph"),
        ], width=6),

        dbc.Col([
            html.H4("Portfolio-Entwicklung"),
            dcc.Graph(id="portfolio-value-graph"),
        ], width=6),
    ], className="mb-4"),

    dbc.Row([
        html.H4("Ergebnis"),
        html.P("Insgesamt: €", id="total-value"),
        html.P("Gewinn: €", id="profit-value"),
    ], className="mb-4"),
])


# Callback für das Update der Diagramme basierend auf der Benutzerauswahl
@app.callback(
    [
        dash.dependencies.Output("stock-price-graph", "figure"),
        dash.dependencies.Output("portfolio-value-graph", "figure"),
        dash.dependencies.Output("total-value", "children"),
        dash.dependencies.Output("profit-value", "children"),
    ],
    [
        dash.dependencies.Input("stock-dropdown", "value"),
        dash.dependencies.Input("strategy-dropdown", "value"),
    ]
)
def update_graphs(symbol, strategy):
    # API-Aufruf für historische Kursdaten
    stock_response = requests.get(f"{API_BASE_URL}/stock/{symbol}")
    stock_data = stock_response.json()
    stock_df = pd.DataFrame(stock_data)

    # API-Aufruf für die gewählte Strategie
    strategy_response = requests.get(f"{API_BASE_URL}/strategy/{strategy}/{symbol}")
    strategy_data = strategy_response.json()
    strategy_df = pd.DataFrame(strategy_data)

    # Aktienkurs-Graph
    stock_fig = px.line(stock_df, x="date", y="close", title=f"Aktienkurs von {symbol}")

    # Portfolio-Wert Graph
    portfolio_fig = px.bar(strategy_df, x="date", y="portfolio_value", title=f"Portfolio-Wert für {symbol}")

    # Berechnung der Ergebnisse
    total_value = f"€{strategy_df['portfolio_value'].iloc[-1]:,.2f}"
    profit_value = f"€{(strategy_df['portfolio_value'].iloc[-1] - strategy_df['portfolio_value'].iloc[0]):,.2f}"

    return stock_fig, portfolio_fig, total_value, profit_value

# Startet das Dash-Server
if __name__ == "__main__":
    app.run_server(debug=True, port=8050)

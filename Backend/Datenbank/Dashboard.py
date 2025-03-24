import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import sqlite3
import pandas as pd
from Backend.strategies.momentum import berechne_momentum_strategie

# Verbindung zur SQLite-Datenbank
DB_NAME = "/Users/jennycao/AQM_Invesment/Backend/Datenbank/DB/investment.db"

# Startkapital für Vergleichsstrategie
STARTKAPITAL = 100000  

def get_all_symbols():
    """Abruf aller verfügbaren Aktien, ETFs und Kryptowährungen aus der Datenbank"""
    conn = sqlite3.connect(DB_NAME)
    query = "SELECT DISTINCT symbol FROM market_data"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df["symbol"].tolist()

# Liste der verfügbaren Symbole aus der Datenbank
symbols = get_all_symbols()
assets = [{"label": symbol, "value": symbol} for symbol in symbols]

# Liste der verfügbaren Strategien
strategies = [
    {"label": "Gleitender Durchschnitt (Moving Average Crossover)", "value": "moving_average"},
    {"label": "Momentum-Strategie", "value": "momentum"},
]

# Dash-App erstellen
app = dash.Dash(__name__)

# Dashboard-Layout
app.layout = html.Div([
    html.H1(id="dashboard-title", style={"textAlign": "center"}),

    html.Div([
        html.Label("Wählen Sie eine Strategie aus:"),
        dcc.Dropdown(
            id="strategy-dropdown",
            options=strategies,
            value="moving_average",
        ),
    ], style={"width": "48%", "display": "inline-block"}),

    html.Div([
        html.Label("Wählen Sie eine Aktie aus:"),
        dcc.Dropdown(
            id="symbol-dropdown",
            options=assets,
            value=symbols[0] if symbols else None
        ),
    ], style={"width": "48%", "display": "inline-block"}),

    html.Div([
        html.H3("Aktueller Aktienkurs"),
        dcc.Graph(id="stock-price-graph"),
    ], style={"width": "48%", "display": "inline-block"}),

    html.Div([
        html.H3("Mein Portfolio"),
        dcc.Graph(id="portfolio-graph"),
    ], style={"width": "48%", "display": "inline-block"}),

    html.Div([
        html.H3("Ergebnis"),
        html.P(id="total-value"),
        html.P(id="profit-value"),
    ], style={"textAlign": "left", "marginTop": "20px"}),
])

# Funktion zum Abrufen von Aktienkursen aus der Datenbank
def get_stock_data(symbol):
    """Abrufen der historischen Kursdaten aus SQLite"""
    conn = sqlite3.connect(DB_NAME)
    query = f"""
        SELECT date, close FROM market_data
        WHERE symbol = '{symbol}'
        ORDER BY date ASC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty:
        return None
    df["date"] = pd.to_datetime(df["date"])
    return df

# Funktion zur Portfolio-Berechnung
def calculate_portfolio(symbol):
    df = get_stock_data(symbol)
    
    if df is None or df.empty:
        return None, 0, 0

    initial_price = df["close"].iloc[0]
    num_shares = STARTKAPITAL / initial_price  # Anzahl der kaufbaren Aktien
    df["portfolio_value"] = df["close"] * num_shares  # Portfolio-Wertberechnung

    final_value = df["portfolio_value"].iloc[-1]
    profit = final_value - STARTKAPITAL
    return df, final_value, profit

# Callback zur Aktualisierung des Dashboard-Titels basierend auf der gewählten Strategie
@app.callback(
    Output("dashboard-title", "children"),
    Input("strategy-dropdown", "value")
)
def update_dashboard_title(selected_strategy):
    """Aktualisiert den Titel des Dashboards basierend auf der gewählten Strategie"""
    if selected_strategy == "moving_average":
        return "Gleitender Durchschnitt Crossover"
    elif selected_strategy == "momentum":
        return " Momentum-Strategie"
    return "Investment-Strategie"

# Callback zur Aktualisierung der Diagramme
@app.callback(
    [Output("stock-price-graph", "figure"),
     Output("portfolio-graph", "figure"),
     Output("total-value", "children"),
     Output("profit-value", "children")],
    Input("symbol-dropdown", "value")
)
def update_dashboard(symbol):
    df_stock = get_stock_data(symbol)
    df_portfolio, total_value, profit = calculate_portfolio(symbol)
    
    # Aktienkurs-Diagramm
    if df_stock is None:
        stock_fig = go.Figure().update_layout(
            title="Fehler: Keine Daten verfügbar!",
            annotations=[{"text": "Keine Daten verfügbar", "x": 0.5, "y": 0.5, "xref": "paper", "yref": "paper"}]
        )
    else:
        stock_fig = go.Figure()
        stock_fig.add_trace(go.Scatter(x=df_stock["date"], y=df_stock["close"], mode="lines", name="Schlusskurs"))
        stock_fig.update_layout(title=f"Aktienkurs für {symbol}", xaxis_title="Datum", yaxis_title="Preis (€)")

    # Portfolio-Diagramm
    if df_portfolio is None:
        portfolio_fig = go.Figure().update_layout(
            title="Fehler: Keine Daten verfügbar!",
            annotations=[{"text": "Keine Daten verfügbar", "x": 0.5, "y": 0.5, "xref": "paper", "yref": "paper"}]
        )
    else:
        portfolio_fig = go.Figure()
        portfolio_fig.add_trace(go.Scatter(x=df_portfolio["date"], y=df_portfolio["portfolio_value"], mode="lines", name="Portfolio-Wert"))
        portfolio_fig.update_layout(title=f"Portfolio-Wert für {symbol}", xaxis_title="Datum", yaxis_title="Wert (€)")

    return stock_fig, portfolio_fig, f"Gesamtwert: € {total_value:,.2f}", f"Gewinn: € {profit:,.2f}"

if __name__ == "__main__":
    app.run_server(debug=True)

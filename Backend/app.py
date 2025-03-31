import sys
import os


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import dash
from dash import dcc, html, Input, Output
from Datenbank.api import get_available_stocks, load_stock_data
from strategies import STRATEGIES

app = dash.Dash(__name__)
app.title = "Investment Strategien"

TICKERS = get_available_stocks()
STRATEGY_NAMES = list(STRATEGIES.keys())

app.layout = html.Div([
    html.H1(id="dashboard-title", style={"textAlign": "center"}),

    html.Div([
        html.Label("Wählen Sie eine Strategie aus:"),
        dcc.Dropdown(
            id='strategy-dropdown',
            options=[{'label': name, 'value': name} for name in STRATEGY_NAMES],
            value=STRATEGY_NAMES[0],
            style={'width': '300px'}
        ),
    ], style={"width": "48%", "display": "inline-block"}),

    html.Div([
        html.Label("Wählen Sie eine Aktie aus:"),
        dcc.Dropdown(
            id='ticker-dropdown',
            options=[{'label': t, 'value': t} for t in TICKERS],
            value=TICKERS[0],
            style={'width': '300px'}
        ),
    ], style={"width": "48%", "display": "inline-block"}),

    html.Div([
        html.H3("Strategie-Performance"),
        dcc.Graph(id='signal-graph', style={"height": "800px"}),
    ], style={"width": "95%","display": "inline-block"}),

    html.Div([
        html.H3("Mein Portfolio"),
        dcc.Graph(id='equity-graph', style={"height": "800px"}),
    ], style={"width": "95%", "display": "inline-block"}),

    html.Div([
        html.H3("Ergebnis"),
        html.P(id="total-value"),
        html.P(id="profit-value"),
    ], style={"textAlign": "left", "marginTop": "20px"}),
])

@app.callback(
    Output('signal-graph', 'figure'),
    Output('equity-graph', 'figure'),
    Output('total-value', 'children'),
    Output('profit-value', 'children'),
    Input('strategy-dropdown', 'value'),
    Input('ticker-dropdown', 'value'),
)

def update_graphs(strategy_name, ticker):
    start_date = "2010-01-01"
    end_date = "2020-12-31"
    df = load_stock_data(ticker, start_date, end_date)
    strategy_func = STRATEGIES[strategy_name]
    fig1, fig2, total, profit = strategy_func(df, start_kapital=100000)
    total_str = f"Gesamtwert am Ende: €{total:,.2f}"
    profit_str = f"Gewinn: €{profit:,.2f}"
    
    return fig1, fig2, total_str, profit_str
@app.callback(
    Output('dashboard-title', 'children'),
    Input('strategy-dropdown', 'value')
)
def update_title(strategy_name):
    return f"{strategy_name}"

if __name__ == '__main__':
    app.run()

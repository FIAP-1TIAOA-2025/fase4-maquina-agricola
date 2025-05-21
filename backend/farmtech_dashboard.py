#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
farm_dashboard.py
Author: Mário (DevOps/SRE) & ChatGPT
Version: 1.11
Date: 2024-05-20

Dashboard web com Dash para visualização dos dados da tabela MedidaSolo do banco farm_data.db.
- Mostra tabela de leituras
- Gráficos de umidade e pH ao longo do tempo
- Atualização automática
- Abre o navegador padrão automaticamente
- Fácil expansão para novos sensores e análises

Licença: MIT
"""

import sqlite3
import pandas as pd
from dash import Dash, html, dcc, dash_table
from dash.dependencies import Input, Output
import plotly.express as px
import webbrowser
import threading
import time

DB_FILE = 'farm_data.db'
DASH_PORT = 8050


def load_medidas():
    """Carrega todas as medições da tabela MedidaSolo em um DataFrame."""
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("""
        SELECT m.id_medida, m.data_hora, m.valor_umidade, m.valor_ph, m.valor_npk,
               m.temperatura, m.previsao_chuva, m.crescimento_percentual,
               d.tipo_sensor, t.nome AS talhao
        FROM MedidaSolo m
        LEFT JOIN DispositivoCampo d ON m.id_dispositivo = d.id_dispositivo
        LEFT JOIN TalhaoCacau t ON m.id_talhao = t.id_talhao
        ORDER BY m.data_hora DESC
    """, conn)
    conn.close()
    return df

app = Dash(__name__)
app.title = "Farm Dashboard - Tech Farm Solutions"

app.layout = html.Div([
    html.H1("Farm Dashboard - Tech Farm Solutions MEM", style={"textAlign": "center"}),
    dcc.Interval(id="interval", interval=5000, n_intervals=0),  # Atualiza a cada 5s
    html.H2("Medições Recentes"),
    dash_table.DataTable(
        id='tabela-medidas',
        columns=[{"name": i, "id": i} for i in [
            "id_medida", "data_hora", "valor_umidade", "valor_ph", "valor_npk", "talhao", "tipo_sensor"
        ]],
        page_size=10,
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'center', 'fontFamily': 'Arial', 'padding': '5px'},
        style_header={'backgroundColor': '#E6F7FF', 'fontWeight': 'bold'},
    ),
    html.Br(),
    html.Div([
        html.Div([
            dcc.Graph(id='grafico-umidade', config={"displayModeBar": False})
        ], style={"width": "48%", "display": "inline-block"}),
        html.Div([
            dcc.Graph(id='grafico-ph', config={"displayModeBar": False})
        ], style={"width": "48%", "display": "inline-block"}),
    ]),
    html.Footer("Autor: Mário (DevOps/SRE) | Versão 1.1 | 2024-05-20", style={"textAlign": "center", "marginTop": "30px"})
])

@app.callback(
    Output('tabela-medidas', 'data'),
    Output('grafico-umidade', 'figure'),
    Output('grafico-ph', 'figure'),
    Input('interval', 'n_intervals')
)
def update_dashboard(n):
    df = load_medidas()
    tabela = df.head(20).to_dict("records")
    fig_umidade = px.line(df.sort_values("data_hora"), x="data_hora", y="valor_umidade", 
                          title="Umidade do Solo ao Longo do Tempo",
                          markers=True, labels={"data_hora": "Data/Hora", "valor_umidade": "Umidade (%)"})
    fig_ph = px.line(df.sort_values("data_hora"), x="data_hora", y="valor_ph", 
                     title="pH do Solo ao Longo do Tempo",
                     markers=True, labels={"data_hora": "Data/Hora", "valor_ph": "pH"})
    fig_umidade.update_layout(xaxis_tickangle=-45)
    fig_ph.update_layout(xaxis_tickangle=-45)
    return tabela, fig_umidade, fig_ph


def open_browser():
    # Aguarda o servidor iniciar e abre o navegador
    time.sleep(1)
    webbrowser.open(f"http://localhost:{DASH_PORT}")

if __name__ == '__main__':
    threading.Thread(target=open_browser).start()
    app.run(debug=True, port=DASH_PORT)
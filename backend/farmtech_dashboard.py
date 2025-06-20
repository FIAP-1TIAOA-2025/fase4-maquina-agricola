#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
farmtech_dashboard.py
Author: Mário (DevOps/SRE) & ChatGPT
Version: 1.15
Date: 2025-05-20

Dashboard web com Dash para visualização dos dados da tabela MedidaSolo do banco farm_data.db.
- Mostra tabela de leituras, incluindo fósforo, potássio e estado do relé
- Gráficos de umidade, fósforo, potássio, pH e relé ao longo do tempo
- Gráfico do relé no estilo "step"/automação SCADA
- Atualização automática
- Abre o navegador padrão automaticamente

Licença: MIT
"""

import sqlite3
import pandas as pd
from dash import Dash, html, dcc, dash_table
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
import re
import webbrowser
import threading
import time

DB_FILE = 'farm_data.db'
DASH_PORT = 8050

def load_medidas():
    """Carrega todas as medições da tabela MedidaSolo em um DataFrame e extrai Fósforo, Potássio e Relé."""

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

    # Extrai fósforo, potássio (0 ou 1) de valor_npk
    def extrai_npk(valor_npk, qual):
        if isinstance(valor_npk, str):
            m = re.search(rf"{qual}:(\d)", valor_npk)
            if m:
                return int(m.group(1))
        return None
    df['fosforo'] = df['valor_npk'].apply(lambda x: extrai_npk(x, 'Fósforo'))
    df['potassio'] = df['valor_npk'].apply(lambda x: extrai_npk(x, 'Potássio'))
    # Estado do relé: espera coluna 'rele' ou pode simular (ajuste conforme seu banco)
    if 'rele' in df.columns:
        df['rele_state'] = df['rele'].map(lambda x: 1 if str(x).upper() in ['1','TRUE','LIGADO'] else 0)
    elif 'valor_npk' in df.columns and df['valor_npk'].str.contains('Relé', na=False).any():
        df['rele_state'] = df['valor_npk'].apply(lambda x: 1 if 'LIGADO' in str(x).upper() else 0)
    else:
        df['rele_state'] = 0
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
            "id_medida", "data_hora", "valor_umidade", "valor_ph", "valor_npk", "fosforo", "potassio", "rele_state", "talhao", "tipo_sensor"

        ]],
        page_size=10,
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'center', 'fontFamily': 'Arial', 'padding': '5px'},
        style_header={'backgroundColor': '#003366', 'color': 'white', 'fontWeight': 'bold'},
        style_data_conditional=[
            {
                "if": {"column_id": "rele_state", "filter_query": "{rele_state} = 1"},
                "backgroundColor": "#D1FFD6",
                "color": "#005500",
            },
            {
                "if": {"column_id": "rele_state", "filter_query": "{rele_state} = 0"},
                "backgroundColor": "#FFD1D1",
                "color": "#770000",
            },
        ],

    ),
    html.Br(),
    html.Div([
        html.Div([
            dcc.Graph(id='grafico-umidade', config={"displayModeBar": False})
        ], style={"width": "48%", "display": "inline-block"}),
        html.Div([
            dcc.Graph(id='grafico-fosforo', config={"displayModeBar": False})
        ], style={"width": "48%", "display": "inline-block"}),
    ]),
    html.Div([
        html.Div([
            dcc.Graph(id='grafico-potassio', config={"displayModeBar": False})
        ], style={"width": "48%", "display": "inline-block"}),
        html.Div([
            dcc.Graph(id='grafico-ph', config={"displayModeBar": False})
        ], style={"width": "48%", "display": "inline-block"}),
    ]),
    html.Div([
        dcc.Graph(id='grafico-rele', config={"displayModeBar": False})
    ], style={"width": "80%", "margin": "auto"}),
    html.Footer("Autor: Mário (DevOps/SRE) | Versão 1.5 | 2024-05-20", style={"textAlign": "center", "marginTop": "30px"})

])

@app.callback(
    Output('tabela-medidas', 'data'),
    Output('grafico-umidade', 'figure'),
    Output('grafico-fosforo', 'figure'),
    Output('grafico-potassio', 'figure'),
    Output('grafico-ph', 'figure'),
    Output('grafico-rele', 'figure'),
    Input('interval', 'n_intervals')
)
def update_dashboard(n):
    df = load_medidas()
    tabela = df.head(20).to_dict("records")
    df_sorted = df.sort_values("data_hora")
    # Umidade
    fig_umidade = px.line(df_sorted, x="data_hora", y="valor_umidade", 
                          title="Umidade do Solo ao Longo do Tempo",
                          markers=True, labels={"data_hora": "Data/Hora", "valor_umidade": "Umidade (%)"})
    # Fósforo
    fig_fosforo = px.line(df_sorted, x="data_hora", y="fosforo", 
                          title="Fósforo Detectado ao Longo do Tempo",
                          markers=True, labels={"data_hora": "Data/Hora", "fosforo": "Fósforo (0/1)"})
    # Potássio
    fig_potassio = px.line(df_sorted, x="data_hora", y="potassio", 
                           title="Potássio Detectado ao Longo do Tempo",
                           markers=True, labels={"data_hora": "Data/Hora", "potassio": "Potássio (0/1)"})
    # pH
    fig_ph = px.line(df_sorted, x="data_hora", y="valor_ph", 
                     title="pH do Solo ao Longo do Tempo",
                     markers=True, labels={"data_hora": "Data/Hora", "valor_ph": "pH"})
    # Relé - gráfico estilo SCADA "step"
    fig_rele = go.Figure()
    fig_rele.add_trace(go.Scatter(
        x=df_sorted["data_hora"], y=df_sorted["rele_state"],
        mode="lines+markers",
        line_shape="hv",
        name="Relé",
        line=dict(width=4, color="green"),
        marker=dict(size=10, color="darkgreen" )
    ))
    fig_rele.update_layout(
        title="Estado do Relé (Step/SCADA)",
        xaxis_title="Data/Hora",
        yaxis_title="Relé (1=LIGADO, 0=DESLIGADO)",
        xaxis_tickangle=-45,
        yaxis=dict(
            tickmode='array',
            tickvals=[0, 1],
            ticktext=['DESLIGADO', 'LIGADO']
        ),
        plot_bgcolor="#F4F4F4",
        height=350
    )
    for fig in [fig_umidade, fig_fosforo, fig_potassio, fig_ph]:
        fig.update_layout(xaxis_tickangle=-45)
    return tabela, fig_umidade, fig_fosforo, fig_potassio, fig_ph, fig_rele

def open_browser():
    time.sleep(1)
    webbrowser.open(f"http://localhost:{DASH_PORT}")

if __name__ == '__main__':
    threading.Thread(target=open_browser).start()
    app.run(debug=True, port=DASH_PORT)

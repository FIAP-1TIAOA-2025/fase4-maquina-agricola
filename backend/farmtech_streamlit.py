#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
farmtech_streamlit.py
Author: Mário (DevOps/SRE) & ChatGPT
Version: 1.18
Date: 2025-05-20
"""

import os
import streamlit as st
import pandas as pd
import sqlite3
import joblib
from datetime import datetime, timedelta
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'models/ml_irrigacao.pkl')
DB_FILE = os.path.join(os.path.dirname(__file__), '../farm_data.db')

st.title("FarmTech Solutions – Dashboard Inteligente de Irrigação")

@st.cache_data(ttl=60)
def load_data():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql("""
        SELECT m.data_hora, m.valor_umidade, m.valor_ph, m.valor_npk, m.temperatura
        FROM MedidaSolo m
        ORDER BY m.data_hora DESC
    """, conn, parse_dates=["data_hora"])
    conn.close()
    df['fosforo'] = df['valor_npk'].str.extract(r"Fósforo:(\d)").astype(float)
    df['potassio'] = df['valor_npk'].str.extract(r"Potássio:(\d)").astype(float)
    df['hour'] = df['data_hora'].dt.hour
    df['weekday'] = df['data_hora'].dt.weekday
    return df

df = load_data()
model = joblib.load(MODEL_PATH)

features = df[['valor_umidade', 'valor_ph', 'fosforo', 'potassio', 'temperatura', 'hour', 'weekday']].fillna(0)
df['ml_predicao'] = model.predict(features)

# --- Filtro temporal (opcional)
st.subheader("Filtro temporal (opcional)")
opcoes = {
    'Última hora': 1,
    'Últimas 6 horas': 6,
    'Últimas 24 horas': 24,
    'Últimos 7 dias': 24 * 7,
    'Últimas 4 semanas': 24 * 7 * 4,
    'Últimos 3 meses': 24 * 30 * 3,
    'Tudo': None
}
escolha = st.selectbox(
    "Selecione o intervalo de tempo:",
    list(opcoes.keys()),
    index=4
)
if opcoes[escolha] is not None:
    inicio = datetime.now() - timedelta(hours=opcoes[escolha])
    df_filtrado = df[df['data_hora'] >= inicio]
else:
    df_filtrado = df.copy()
st.write(f"Mostrando dados para: **{escolha}**")

# --- GRÁFICO: Sensores Coletados (Plotly interativo com range slider) ---
st.subheader("Histórico dos sensores (interativo)")
fig_sensores = go.Figure()
fig_sensores.add_trace(go.Scatter(
    x=df_filtrado['data_hora'], y=df_filtrado['valor_umidade'], name="Umidade", mode="lines+markers"
))
fig_sensores.add_trace(go.Scatter(
    x=df_filtrado['data_hora'], y=df_filtrado['valor_ph'], name="pH", mode="lines+markers"
))
fig_sensores.add_trace(go.Scatter(
    x=df_filtrado['data_hora'], y=df_filtrado['fosforo'], name="Fósforo", mode="lines+markers"
))
fig_sensores.add_trace(go.Scatter(
    x=df_filtrado['data_hora'], y=df_filtrado['potassio'], name="Potássio", mode="lines+markers"
))
fig_sensores.update_layout(
    xaxis_title="Data/Hora",
    yaxis_title="Valor",
    legend_title="Sensor",
    height=400,
    hovermode='x unified',
    xaxis=dict(
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1d", step="day", stepmode="backward"),
                dict(count=7, label="1w", step="day", stepmode="backward"),
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(step="all")
            ])
        ),
        rangeslider=dict(visible=True),
        type="date"
    )
)
st.plotly_chart(fig_sensores, use_container_width=True)

# --- GRÁFICO: Predição ML nos dados coletados (Plotly interativo com range slider) ---
st.subheader("Previsão ML de irrigação nos dados coletados (interativo)")
fig_pred = px.line(df_filtrado, x='data_hora', y='ml_predicao', markers=True, title="Predição ML de Irrigação")
fig_pred.update_layout(
    xaxis_title="Data/Hora",
    yaxis_title="Irrigar (1=sim, 0=não)",
    height=300,
    hovermode='x unified',
    xaxis=dict(
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1d", step="day", stepmode="backward"),
                dict(count=7, label="1w", step="day", stepmode="backward"),
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(step="all")
            ])
        ),
        rangeslider=dict(visible=True),
        type="date"
    )
)
st.plotly_chart(fig_pred, use_container_width=True)

st.dataframe(df_filtrado[['data_hora','valor_umidade','valor_ph','fosforo','potassio','ml_predicao']].head(30))

# --- PREVISÃO FUTURA por períodos/dias ---
st.subheader("Previsão futura: melhores períodos para irrigar")
opcoes_horizonte = {
    'Próximo 1 dia': 1,
    'Próximos 7 dias': 7,
    'Próximas 4 semanas': 28,
    'Próximos 3 meses': 90
}
esc_horiz = st.selectbox("Selecione o horizonte de previsão:", list(opcoes_horizonte.keys()), index=0)
dias_futuro = opcoes_horizonte[esc_horiz]

if not df_filtrado.empty:
    last = df_filtrado.iloc[0]
    data_hoje = datetime.now().replace(minute=0, second=0, microsecond=0)
    future_rows = []
    for dia in range(dias_futuro):
        for h in range(0, 24, 1):  # a cada hora
            dt_fut = data_hoje + timedelta(days=dia, hours=h)
            future_rows.append({
                'data_hora': dt_fut,
                'hour': dt_fut.hour,
                'weekday': dt_fut.weekday(),
                'valor_umidade': last['valor_umidade'],
                'valor_ph': last['valor_ph'],
                'fosforo': last['fosforo'],
                'potassio': last['potassio'],
                'temperatura': last['temperatura']
            })
    df_future = pd.DataFrame(future_rows)
    features_future = df_future[['valor_umidade', 'valor_ph', 'fosforo', 'potassio', 'temperatura', 'hour', 'weekday']].fillna(0)
    df_future['previsto_irrigar'] = model.predict(features_future)

    def periodo(h):
        if 0 <= h < 6: return "Madrugada"
        elif 6 <= h < 12: return "Manhã"
        elif 12 <= h < 18: return "Tarde"
        else: return "Noite"
    df_future['periodo'] = df_future['hour'].apply(periodo)
    df_future['dia'] = df_future['data_hora'].dt.date

    resumo = df_future.groupby(['dia', 'periodo'])['previsto_irrigar'].mean().reset_index()
    resumo_pivot = resumo.pivot(index='dia', columns='periodo', values='previsto_irrigar').fillna(0)

    st.subheader("Tabela de previsão média de irrigação por período")
    st.dataframe(resumo_pivot.style.format("{:.2f}"))

    melhores = resumo_pivot.idxmax(axis=1)
    st.write("**Melhor período para irrigar em cada dia:**")
    st.write(melhores.value_counts().rename_axis('Período').reset_index(name='Dias em destaque'))

    st.subheader("Evolução da previsão de irrigação por período (interativo)")
    fig_future = go.Figure()
    for periodo_nome in resumo['periodo'].unique():
        fig_future.add_trace(go.Scatter(
            x=resumo_pivot.index,
            y=resumo_pivot[periodo_nome],
            mode='lines+markers',
            name=periodo_nome
        ))
    fig_future.update_layout(
        xaxis_title="Data",
        yaxis_title="Média da previsão (1=irrigar, 0=não irrigar)",
        hovermode='x unified',
        height=400,
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1d", step="day", stepmode="backward"),
                    dict(count=7, label="1w", step="day", stepmode="backward"),
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(step="all")
                ])
            ),
            rangeslider=dict(visible=True),
            type="date"
        )
    )
    st.plotly_chart(fig_future, use_container_width=True)

    with st.expander("Ver detalhes das previsões futuras (hora a hora)"):
        st.dataframe(df_future[['data_hora', 'periodo', 'previsto_irrigar']].head(100))

st.info("Todos os gráficos permitem zoom, pan e seleção de datas diretamente no gráfico. Previsões são baseadas nos dados mais recentes coletados.")

st.write("""
Legenda dos períodos:  
- Madrugada = 00h–05h  
- Manhã = 06h–11h  
- Tarde = 12h–17h  
- Noite = 18h–23h
""")

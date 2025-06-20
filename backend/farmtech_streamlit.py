#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
farmtech_streamlit.py
Author: Mário (DevOps/SRE) & ChatGPT
Version: 1.18
Date: 2025-05-20
"""

import streamlit as st
import sqlite3
import pandas as pd
import joblib
import os

st.title("FarmTech Solutions – Irrigation Dashboard com ML")

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'models/ml_irrigacao.pkl')
DB_FILE = os.path.join(os.path.dirname(__file__), '../farm_data.db')

@st.cache_data(ttl=20)
def load_data():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql("""
        SELECT m.data_hora, m.valor_umidade, m.valor_ph, m.valor_npk, m.temperatura, a.recomendacao
        FROM MedidaSolo m LEFT JOIN AcaoAgricola a USING(id_medida)
        ORDER BY m.data_hora DESC
    """, conn, parse_dates=["data_hora"])
    conn.close()
    df['fosforo'] = df['valor_npk'].str.extract(r"Fósforo:(\d)").astype(float)
    df['potassio'] = df['valor_npk'].str.extract(r"Potássio:(\d)").astype(float)
    return df

df = load_data()

# Carrega o modelo e faz a predição
model = joblib.load(MODEL_PATH)
features = df[['valor_umidade', 'valor_ph', 'temperatura','fosforo', 'potassio' ]].fillna(0)
df['ml_predicao'] = model.predict(features)

st.subheader("Gráfico de Umidade, pH, Fósforo, Potássio")
st.line_chart(df.set_index('data_hora')[['valor_umidade', 'valor_ph', 'fosforo', 'potassio']])

st.subheader("Ação Recomendada pelo Modelo (1 = irrigar, 0 = não irrigar)")
st.line_chart(df.set_index('data_hora')['ml_predicao'])

st.write("Últimas recomendações:")
st.dataframe(df[['data_hora','valor_umidade','valor_ph','fosforo','potassio','ml_predicao']].head(10))

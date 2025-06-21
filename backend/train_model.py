#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
farmtech_coleta_dados.py
Author: Mário (DevOps/SRE) & ChatGPT
Version: 1.17

Date: 2025-05-20

Licença: MIT

# train_model.py
"""

import sqlite3
import pandas as pd
import joblib
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import TimeSeriesSplit, GridSearchCV
import os

DB_FILE = os.path.join(os.path.dirname(__file__), '../farm_data.db')
MODEL_FILE = os.path.join(os.path.dirname(__file__), 'models/ml_irrigacao.pkl')

conn = sqlite3.connect(DB_FILE)
df = pd.read_sql(
    "SELECT id_medida, data_hora, valor_umidade, valor_ph, valor_npk, temperatura FROM MedidaSolo",
    conn, parse_dates=["data_hora"])
conn.close()

# Extrair fósforo e potássio do valor_npk
df['fosforo'] = df['valor_npk'].str.extract(r"Fósforo:(\d)").astype(float)
df['potassio'] = df['valor_npk'].str.extract(r"Potássio:(\d)").astype(float)

# Adicionar hora do dia e dia da semana
df['hour'] = df['data_hora'].dt.hour
df['weekday'] = df['data_hora'].dt.weekday

# Target do relé conforme sua lógica
df['rele_state'] = (
    (df['fosforo'] == 1) &
    (df['potassio'] == 1) &
    (df['valor_umidade'] < 40.0) &
    (df['valor_ph'] > 5.5) &
    (df['valor_ph'] < 6.5)
).astype(int)

print("Distribuição do target (rele_state):")
print(df['rele_state'].value_counts())

# Features e target
X = df[['valor_umidade', 'valor_ph', 'fosforo', 'potassio', 'temperatura', 'hour', 'weekday']].fillna(0)
y = df['rele_state']

# Treinamento do modelo
tscv = TimeSeriesSplit(n_splits=3)
model = HistGradientBoostingClassifier()
grid = GridSearchCV(model, {"learning_rate": [0.01, 0.1]}, cv=tscv)
grid.fit(X, y)
joblib.dump(grid.best_estimator_, MODEL_FILE)
print(f"Modelo salvo como {MODEL_FILE}. Target = relé.")

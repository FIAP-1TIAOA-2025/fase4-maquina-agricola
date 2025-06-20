#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
farmtech_coleta_dados.py
Author: Mário (DevOps/SRE) & ChatGPT
Version: 1.17

Date: 2025-05-20

Licença: MIT
"""
# train_model.py
import sqlite3
import os
import pandas as pd
import joblib
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import TimeSeriesSplit, GridSearchCV

DB_FILE = os.path.join(os.path.dirname(__file__), '../farm_data.db')
MODEL_FILE = os.path.join(os.path.dirname(__file__), 'models/ml_irrigacao.pkl')

conn = sqlite3.connect(DB_FILE)
df = pd.read_sql("SELECT id_medida, data_hora, valor_umidade, valor_ph, valor_npk, temperatura FROM MedidaSolo", conn)
acao = pd.read_sql("SELECT id_acao, id_medida FROM AcaoAgricola", conn)
conn.close()

df = df.merge(acao[['id_medida']].assign(acao=1), how='left', on='id_medida').fillna(0)
df['fosforo'] = df['valor_npk'].str.extract(r"Fósforo:(\d)").astype(int)
df['potassio'] = df['valor_npk'].str.extract(r"Potássio:(\d)").astype(int)

X = df[['valor_umidade','valor_ph','fosforo','potassio','temperatura']]
y = df['acao']
tscv = TimeSeriesSplit(n_splits=5)
model = HistGradientBoostingClassifier()
grid = GridSearchCV(model, {"learning_rate":[0.01,0.1]}, cv=tscv)
grid.fit(X, y)
joblib.dump(grid.best_estimator_, MODEL_FILE)

# train_model.py
import sqlite3
import pandas as pd
import joblib
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import TimeSeriesSplit, GridSearchCV

conn = sqlite3.connect('farm_data.db')
df = pd.read_sql("SELECT id_medida, data_hora, valor_umidade, valor_ph, valor_npk, temperatura FROM MedidaSolo", conn)
acao = pd.read_sql("SELECT id_acao, id_medida FROM AcaoAgricola", conn)
conn.close()

df = df.merge(acao[['id_medida']].assign(acao=1), how='left', on='id_medida').fillna(0)
df['phosphorus'] = df['valor_npk'].str.extract(r"Fósforo:(\d)").astype(int)
df['potassium'] = df['valor_npk'].str.extract(r"Potássio:(\d)").astype(int)

X = df[['valor_umidade','valor_ph','temperatura','phosphorus','potassium']]
y = df['acao']
tscv = TimeSeriesSplit(n_splits=5)
model = HistGradientBoostingClassifier()
grid = GridSearchCV(model, {"learning_rate":[0.01,0.1]}, cv=tscv)
grid.fit(X, y)
joblib.dump(grid.best_estimator_, 'models/irrigation_model.pkl')

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
simular_dados.py
Author: Mário (DevOps/SRE) & ChatGPT
Version: 1.19
Date: 2025-06-20
"""

import csv
import random
from datetime import datetime, timedelta
import numpy as np
from tqdm import tqdm
import argparse
import os
import sqlite3

DB_FILE = os.path.join(os.path.dirname(__file__), '../farm_data.db')

def simula_leitura(dt):
    hour = dt.hour

    # Umidade: mais baixa ao meio-dia, maior à noite/madrugada
    base_umidade = 38 + 6 * np.sin(2 * np.pi * ((hour + dt.minute/60)/24))
    ruido = random.uniform(-2, 2)
    umidade = base_umidade + ruido

    # Fósforo/Potássio: maioria 1, mas pode variar
    fosforo = 1 if random.random() > 0.1 else 0
    potassio = 1 if random.random() > 0.1 else 0

    # pH: maioria em torno de 6.0
    ph = random.uniform(5.0, 7.0)

    # Temperatura: mais quente de dia, fria de madrugada
    temperatura = 20 + 10 * np.sin(2 * np.pi * ((hour-6) / 24)) + random.uniform(-2,2)

    # Previsão de chuva: maioria 'Não'
    chuva = 'Sim' if random.random() > 0.97 else 'Não'
    crescimento = random.uniform(0, 100)

    # Valor NPK string
    valor_npk = f"Fósforo:{fosforo},Potássio:{potassio}"

    return [
        dt.strftime("%Y-%m-%d %H:%M:%S"),
        round(umidade, 2),
        round(ph, 2),
        valor_npk,
        round(temperatura, 1),
        chuva,
        round(crescimento, 1),
        1,  # id_dispositivo
        1   # id_talhao
    ]

def sorteia_periodo():
    # 0: Madrugada (0-5), 1: Manhã (6-11), 2: Tarde (12-17), 3: Noite (18-23)
    return random.choice([0, 1, 2, 3])

def simular_para_csv_e_ou_banco(dias=90, freq=1, csv_file="dados_simulados.csv", inserir_no_banco=False, db_file=DB_FILE):
    total_segundos = dias * 24 * 60 * 60
    N = int(total_segundos / freq)
    start = datetime.now() - timedelta(seconds=N)
    header = [
        "data_hora", "valor_umidade", "valor_ph", "valor_npk",
        "temperatura", "previsao_chuva", "crescimento_percentual",
        "id_dispositivo", "id_talhao"
    ]

    # Determina o melhor período para cada dia
    periodos_nome = {0: "Madrugada", 1: "Manhã", 2: "Tarde", 3: "Noite"}
    melhor_periodo_por_dia = dict()
    start_date = (datetime.now() - timedelta(seconds=N)).date()
    #start_date = start_datetime.date()
    for d in range(dias + 1):
        melhor_periodo_por_dia[start_date + timedelta(days=d)] = sorteia_periodo()

    print("Melhor período de irrigação por dia (randomizado):")
    for k, v in list(melhor_periodo_por_dia.items())[:min(5, dias)]:
        print(f"{k}: {periodos_nome[v]}")
    if dias > 5:
        print("...")

    print(f"Simulando {N} leituras (dias={dias}, freq={freq}s)...")
    if inserir_no_banco:
        conn = sqlite3.connect(db_file)
        c = conn.cursor()

    with open(csv_file, "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        batch = []
        for i in tqdm(range(N)):
            dt = start + timedelta(seconds=i * freq)
            row = simula_leitura(dt)
            hour = dt.hour
            dia = dt.date()
            periodo_aleatorio = melhor_periodo_por_dia[dia]  # 0: Madrugada, 1: Manhã, 2: Tarde, 3: Noite
            if periodo_aleatorio == 0:
                periodo_horas = range(0,6)
            elif periodo_aleatorio == 1:
                periodo_horas = range(6,12)
            elif periodo_aleatorio == 2:
                periodo_horas = range(12,18)
            else:
                periodo_horas = range(18,24)
            # Reforça exemplos positivos apenas no melhor período sorteado do dia
            repetir = 3 if (
                row[1] < 40.0 and
                row[2] > 5.5 and row[2] < 6.5 and
                row[3] == "Fósforo:1,Potássio:1" and
                hour in periodo_horas
            ) else 1
            for _ in range(repetir):
                writer.writerow(row)
                if inserir_no_banco:
                    batch.append(tuple(row))
                if inserir_no_banco and len(batch) >= 5000:
                    c.executemany("""
                        INSERT INTO MedidaSolo (
                            data_hora, valor_umidade, valor_ph, valor_npk,
                            temperatura, previsao_chuva, crescimento_percentual,
                            id_dispositivo, id_talhao
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, batch)
                    conn.commit()
                    batch = []
        # Insere o restante do batch
        if inserir_no_banco and batch:
            c.executemany("""
                INSERT INTO MedidaSolo (
                    data_hora, valor_umidade, valor_ph, valor_npk,
                    temperatura, previsao_chuva, crescimento_percentual,
                    id_dispositivo, id_talhao
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, batch)
            conn.commit()
            conn.close()
    print(f"Arquivo gerado com sucesso: {os.path.abspath(csv_file)}")
    if inserir_no_banco:
        print(f"Dados também inseridos no banco: {db_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simula dados de sensores FarmTech em CSV e/ou banco de dados.")
    parser.add_argument('--dias', type=int, default=90, help='Quantidade de dias a simular (default: 90)')
    parser.add_argument('--freq', type=int, default=1, help='Frequência em segundos (default: 1)')
    parser.add_argument('--csv', type=str, default="dados_simulados.csv", help='Nome do arquivo CSV de saída')
    parser.add_argument('--insert-db', action='store_true', help='Também insere os dados no banco de dados SQLite')
    parser.add_argument('--db', type=str, default=DB_FILE, help='Caminho do banco SQLite')
    args = parser.parse_args()
    simular_para_csv_e_ou_banco(
        dias=args.dias,
        freq=args.freq,
        csv_file=args.csv,
        inserir_no_banco=args.insert_db,
        db_file=args.db
    )

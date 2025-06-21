#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
farmtech_coleta_dados.py
Author: Mário (DevOps/SRE) & ChatGPT
Version: 1.7

Date: 2025-05-20

Integração ESP32 (Wokwi ) com banco MER completo em SQLite.
- Cria tabelas se necessário
- Garante integridade relacional
- Insere dados do serial em MedidaSolo
- Pronto para uso didático e produção simples

Este código é parte do projeto FarmTech, um sistema de monitoramento e controle agrícola.
MER original não foi modificado, apenas adaptado para SQLite.

Licença: MIT
"""

import sqlite3
from datetime import datetime
import serial
import re
import os
import joblib
import pandas as pd

DB_FILE = os.path.join(os.path.dirname(__file__), '../farm_data.db')
# Para Wokwi RFC2217: 'rfc2217://localhost:8180'
# Para hardware real (Linux): '/dev/ttyUSB0', '/dev/ttyACM0'
# Para hardware real (Windows): 'COM3', 'COM4', etc.
SERIAL_URL = 'rfc2217://localhost:8181'
BAUDRATE = 115200
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'models/ml_irrigacao.pkl')

def inicializa_banco():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("PRAGMA foreign_keys = ON;")
    # Cultura
    c.execute("""
        CREATE TABLE IF NOT EXISTS Cultura (
            id_cultura INTEGER PRIMARY KEY,
            nome VARCHAR(100),
            nutriente_principal VARCHAR(100)
        );
    """)
    # DispositivoCampo
    c.execute("""
        CREATE TABLE IF NOT EXISTS DispositivoCampo (
            id_dispositivo INTEGER PRIMARY KEY,
            tipo_sensor VARCHAR(50),
            descricao VARCHAR(255)
        );
    """)
    # TalhaoCacau
    c.execute("""
        CREATE TABLE IF NOT EXISTS TalhaoCacau (
            id_talhao INTEGER PRIMARY KEY,
            nome VARCHAR(100),
            regiao VARCHAR(100),
            produtor VARCHAR(100),
            id_cultura INTEGER,
            FOREIGN KEY (id_cultura) REFERENCES Cultura(id_cultura)
        );
    """)
    # MedidaSolo
    c.execute("""
        CREATE TABLE IF NOT EXISTS MedidaSolo (
            id_medida INTEGER PRIMARY KEY,
            data_hora DATETIME,
            valor_umidade DOUBLE,
            valor_ph DOUBLE,
            valor_npk VARCHAR(100),
            temperatura DOUBLE,
            previsao_chuva VARCHAR(20),
            crescimento_percentual DOUBLE,
            id_dispositivo INTEGER,
            id_talhao INTEGER,
            FOREIGN KEY (id_dispositivo) REFERENCES DispositivoCampo(id_dispositivo),
            FOREIGN KEY (id_talhao) REFERENCES TalhaoCacau(id_talhao)
        );
    """)
    # AcaoAgricola
    c.execute("""
        CREATE TABLE IF NOT EXISTS AcaoAgricola (
            id_acao INTEGER PRIMARY KEY,
            id_medida INTEGER,
            recomendacao VARCHAR(255),
            FOREIGN KEY (id_medida) REFERENCES MedidaSolo(id_medida)
        );
    """)
    # HistoricoAcao
    c.execute("""
        CREATE TABLE IF NOT EXISTS HistoricoAcao (
            id_historico INTEGER PRIMARY KEY,
            id_acao INTEGER,
            executada BOOLEAN,
            data_execucao DATETIME,
            observacao_produtor VARCHAR(255),
            FOREIGN KEY (id_acao) REFERENCES AcaoAgricola(id_acao)
        );
    """)
    conn.commit()
    conn.close()

def insere_se_necessario():
    """Insere registros padrões em Cultura, DispositivoCampo e TalhaoCacau, se necessário."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("PRAGMA foreign_keys = ON;")
    # Cultura
    c.execute("SELECT COUNT(*) FROM Cultura")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO Cultura (id_cultura, nome, nutriente_principal) VALUES (1, 'Cacau', 'Fósforo')")
    # DispositivoCampo
    c.execute("SELECT COUNT(*) FROM DispositivoCampo")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO DispositivoCampo (id_dispositivo, tipo_sensor, descricao) VALUES (1, 'ESP32', 'Simulador Wokwi')")
    # TalhaoCacau
    c.execute("SELECT COUNT(*) FROM TalhaoCacau")
    if c.fetchone()[0] == 0:
        c.execute("""INSERT INTO TalhaoCacau (id_talhao, nome, regiao, produtor, id_cultura)
                     VALUES (1, 'Talhão 1', 'Região A', 'Produtor X', 1)""")
    conn.commit()
    conn.close()

def inserir_medida_solo(umidade, ph, fosforo, potassio, sensor1, sensor2,
                        temperatura=None, previsao_chuva=None, crescimento_percentual=None,
                        id_dispositivo=1, id_talhao=1):
    """
    Insere uma leitura na tabela MedidaSolo, adaptando dados do ESP32/Wokwi para o MER.
    valor_npk armazena string como 'Fósforo:1,Potássio:0'
    """
    valor_npk = f"Fósforo:{int(fosforo)},Potássio:{int(potassio)}"
    data_hora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("PRAGMA foreign_keys = ON;")
    c.execute("""
        INSERT INTO MedidaSolo (
            data_hora, valor_umidade, valor_ph, valor_npk,
            temperatura, previsao_chuva, crescimento_percentual,
            id_dispositivo, id_talhao
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data_hora, umidade, ph, valor_npk, temperatura,
        previsao_chuva, crescimento_percentual, id_dispositivo, id_talhao
    ))
    conn.commit()
    conn.close()

def parse_serial_line(line):
    pattern = r"Fósforo:\s*(\d)\s*\|\s*Potássio:\s*(\d)\s*\|\s*Umidade:\s*([0-9.]+)\s*\|\s*pH\s*\(sim\):\s*([0-9.]+)\s*\|\s*Relé:\s*(LIGADO|DESLIGADO)"
    m = re.match(pattern, line)
    if not m:
        return None
    fosforo = bool(int(m.group(1)))
    potassio = bool(int(m.group(2)))
    umidade = float(m.group(3))
    ph = float(m.group(4))
    rele = True if m.group(5) == 'LIGADO' else False
    # Pode retornar valores extras (None) para campos não presentes no print
    # sensor1, sensor2, temperatura, etc. podem ser definidos como None aqui
    return umidade, ph, fosforo, potassio, None, None  # sensor1, sensor2 = None

#def parse_serial_line(line):
#    """
#    Recebe linha no formato:
#    Fósforo: 1 | Potássio: 0 | Umidade: 37.2 | pH (sim): 6.32 | Sensor1: 1800 | Sensor2: 2500 | Relé: LIGADO
#    """
#    pattern = r"Fósforo:\s*(\d) \| Potássio:\s*(\d) \| Umidade:\s*([0-9.]+|nan) \| pH.*?:\s*([0-9.]+) \| Sensor1:\s*(\d+) \| Sensor2:\s*(\d+)"
#    m = re.match(pattern, line)
#    if not m:
#        return None
#    fosforo = bool(int(m.group(1)))
#    potassio = bool(int(m.group(2)))
#    umidade = float(m.group(3))
#    ph = float(m.group(4))
#    sensor1 = int(m.group(5))
#    sensor2 = int(m.group(6))
#    return umidade, ph, fosforo, potassio, sensor1, sensor2

def main():
    inicializa_banco()
    insere_se_necessario()
    print(f"Conectando ao serial {SERIAL_URL} ...")
    ser = serial.serial_for_url(SERIAL_URL, baudrate=BAUDRATE, timeout=2)
    model = joblib.load(MODEL_PATH)
    while True:
        try:
            line = ser.readline().decode("utf-8").strip()
            if not line:
                continue
            print("Recebido:", line)
            data = parse_serial_line(line)
            if data:
                umidade, ph, fosforo, potassio, *_ = data
                temperatura = None  # adapte se houver
                inserir_medida_solo(
                    umidade, ph, fosforo, potassio, None, None, temperatura=temperatura
                )
                # ==== INFERÊNCIA ML ====
                # Para desenvolvimento futuro quando o ML vai dizer quando irrigar
                # Colocar em uma nova  tabela, não em AcaoAgricola
                # Agora o modelo é muito analítico, é muito claro qunando irrigar
                # So faz sentido inferencia se coletar mais dados de resultados da colheita com os dados dos sensores

                #now = pd.to_datetime(datetime.now())
                #features = pd.DataFrame([[umidade, ph, int(fosforo), int(potassio), temperatura or 0, now.hour, now.weekday()]],
                #                        columns=['valor_umidade', 'valor_ph', 'fosforo', 'potassio', 'temperatura', 'hour', 'weekday'])
                #pred = int(model.predict(features)[0])
                #print(f"pred: {model.predict(features)}")
                ## Registre a recomendação do modelo
                #conn = sqlite3.connect(DB_FILE)
                #c = conn.cursor()
                #c.execute("SELECT last_insert_rowid()")
                #idm = c.fetchone()[0]
                #c.execute("INSERT INTO AcaoAgricola (id_medida, recomendacao) VALUES (?, ?)", (idm, str(pred)))
                #conn.commit()
                #conn.close()
                #print(f">> Medida e recomendação ML ({pred}) inseridas.")

            else:
                print(">> Linha não reconhecida/formato inválido.")
        except KeyboardInterrupt:
            print("Parado pelo usuário.")
            break
        except Exception as e:
            print("Erro:", e)
            continue

if __name__ == "__main__":
    main()

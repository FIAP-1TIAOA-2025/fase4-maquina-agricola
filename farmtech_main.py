#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
farmtech_main.py
Author: Mário (DevOps/SRE) & ChatGPT
Version: 1.5
Date: 2025-06-20

Menu interativo: Treina ML, coleta dados em background, faz tail dos logs, tail do serial Wokwi, inicia dashboard Streamlit.
"""

import subprocess
import os
import sys
import time
from datetime import datetime

BACKEND_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend'))
WOKWI_TOML = os.path.join(os.path.dirname(__file__), 'wokwi.toml')
coleta_proc = None
log_file = None

def start_script(script_name, streamlit=False, log_to_file=False):
    script_path = os.path.join(BACKEND_PATH, script_name)
    if streamlit:
        print(f"Iniciando dashboard Streamlit: {script_path}")
        return subprocess.Popen(['streamlit', 'run', script_path], cwd=BACKEND_PATH)
    elif log_to_file:
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(BACKEND_PATH, f"coleta_log_{now}.txt")
        os.makedirs(BACKEND_PATH, exist_ok=True)
        print(f"Iniciando coleta de dados, logs em: {log_file}")
        f = open(log_file, "w")
        proc = subprocess.Popen([sys.executable, '-u', script_path], stdout=f, stderr=subprocess.STDOUT, cwd=BACKEND_PATH)
        return proc, log_file
    else:
        print(f"Executando script: {script_path}")
        return subprocess.Popen([sys.executable, script_path], cwd=BACKEND_PATH)

def menu():
    print("="*60)
    print(" FarmTech Solutions – Menu Principal ".center(60, "="))
    print("="*60)
    print("1 - Treinar modelo ML com dados do banco")
    print("2 - Iniciar coleta de dados em background (log em arquivo)")
    print("3 - Parar coleta de dados")
    print("4 - Tail no log de coleta de dados")
    print("5 - Tail no serial do Wokwi (RFC2217)")
    print("6 - Iniciar dashboard Streamlit")
    print("7 - Sair")
    print("="*60)

def tail_file(file_path, n=20):
    try:
        print(f"\n---- Mostrando últimas linhas de {file_path} ----")
        with open(file_path, 'r') as f:
            # Move para o final do arquivo
            f.seek(0, os.SEEK_END)
            size = f.tell()
            f.seek(max(size-4096, 0), os.SEEK_SET)
            lines = f.readlines()[-n:]
            for line in lines:
                print(line, end='')
        print("---- Pressione Ctrl+C para sair do tail ----\n")
        with open(file_path, 'r') as f:
            f.seek(0, os.SEEK_END)
            while True:
                line = f.readline()
                if line:
                    print(line, end='')
                else:
                    time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n(Tail encerrado pelo usuário)")
    except Exception as e:
        print(f"Erro no tail: {e}")

def tail_serial_wokwi():
    import re
    try:
        with open(WOKWI_TOML, "r") as f:
            content = f.read()
        port = None
        match = re.search(r"rfc2217ServerPort\s*=\s*(\d+)", content)
        if match:
            port = int(match.group(1))
        else:
            print("Porta RFC2217 não encontrada no wokwi.toml.")
            return
        print(f"Fazendo tail no serial RFC2217 (porta {port})...")
        print("Pressione Ctrl+C para sair.")
        # Usa netcat/telnet conforme SO
        if sys.platform.startswith("win"):
            os.system(f"telnet localhost {port}")
        else:
            os.system(f"nc localhost {port}")
    except Exception as e:
        print(f"Erro lendo wokwi.toml: {e}")

def main():
    global coleta_proc, log_file
    while True:
        menu()
        escolha = input("Escolha uma opção [1-7]: ").strip()
        if escolha == "1":
            print("Treinando modelo ML (train_model.py)...")
            proc = start_script("train_model.py")
            proc.wait()
            print("Treinamento finalizado.")
        elif escolha == "2":
            if coleta_proc is not None and coleta_proc.poll() is None:
                print("Coleta de dados já está em execução (PID {}).".format(coleta_proc.pid))
            else:
                coleta_proc, log_file = start_script("farmtech_coleta_dados.py", log_to_file=True)
                print(f"Coleta de dados iniciada em background (PID {coleta_proc.pid}). Log: {log_file}")
        elif escolha == "3":
            if coleta_proc is not None and coleta_proc.poll() is None:
                print(f"Parando coleta de dados (PID {coleta_proc.pid})...")
                coleta_proc.terminate()
                coleta_proc.wait(timeout=5)
                print("Coleta parada.")
                coleta_proc = None
            else:
                print("Nenhuma coleta de dados em execução.")
        elif escolha == "4":
            if log_file and os.path.exists(log_file):
                tail_file(log_file)
            else:
                print("Nenhum log de coleta encontrado ou coleta ainda não iniciada.")
        elif escolha == "5":
            tail_serial_wokwi()
        elif escolha == "6":
            print("Iniciando dashboard Streamlit...")
            proc = start_script("farmtech_streamlit.py", streamlit=True)
            print("Pressione CTRL+C para finalizar o dashboard.")
            try:
                proc.wait()
            except KeyboardInterrupt:
                print("Finalizando dashboard...")
                proc.terminate()
                proc.wait()
        elif escolha == "7":
            if coleta_proc is not None and coleta_proc.poll() is None:
                print("Parando coleta de dados antes de sair...")
                coleta_proc.terminate()
                coleta_proc.wait(timeout=5)
                print("Coleta parada.")
            print("Saindo...")
            break
        else:
            print("Opção inválida. Escolha entre 1 e 7.")

if __name__ == "__main__":
    main()

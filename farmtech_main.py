#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
farmtech_main.py
Author: Mário (DevOps/SRE) & ChatGPT
Version: 1.2
Date: 2025-05-20

Script principal para iniciar o coletor de dados (farmtech_coleta_dados.py)
e o dashboard (farmtech_dashboard.py) simultaneamente.
"""

import subprocess
import os
import sys
import time

BACKEND_PATH = os.path.join(os.path.dirname(__file__), 'backend')

def start_script(script_name):
    # Garante o caminho correto
    script_path = os.path.join(BACKEND_PATH, script_name)
    # Usa o mesmo Python da execução principal
    return subprocess.Popen([sys.executable, script_path])

if __name__ == "__main__":
    print("Treinando ML com dados existentes no banco")
    training_proc = start_script("train_model.py")
    print("Iniciando coleta de dados...")
    coleta_proc = start_script("farmtech_coleta_dados.py")
    # Espera 2 segundos para garantir que dados serão gravados antes do dashboard iniciar
    time.sleep(2)
    print("Iniciando dashboard...")
    dash_proc = start_script("farmtech_dashboard.py")
    print("Todos os serviços estão rodando. Use CTRL+C para finalizar.")

    try:
        # Espera ambos os processos
        training_proc.wait()
        dash_proc.wait()
        coleta_proc.wait()
    except KeyboardInterrupt:
        print("Encerrando scripts...")
        coleta_proc.terminate()
        dash_proc.terminate()
        coleta_proc.wait()
        dash_proc.wait()
        print("Finalizado.")

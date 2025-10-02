# core/desempenho.py

import json
from datetime import datetime

class Desempenho:
    def __init__(self, stake_base, file_path="desempenho.json"):
        self.stake_base = stake_base
        self.file_path = file_path
        self.saldo_atual = 0.0
        self.total_ganhos = 0.0
        self.total_perdas = 0.0
        self.operacoes_ganhas = 0
        self.operacoes_perdidas = 0
        self.data_ultima_atualizacao = str(datetime.now())
        self.carregar()

    def carregar(self):
        try:
            with open(self.file_path, 'r') as f:
                data = json.load(f)
                self.saldo_atual = data.get("saldo_atual", 0.0)
                self.total_ganhos = data.get("total_ganhos", 0.0)
                self.total_perdas = data.get("total_perdas", 0.0)
                self.operacoes_ganhas = data.get("operacoes_ganhas", 0)
                self.operacoes_perdidas = data.get("operacoes_perdidas", 0)
                self.data_ultima_atualizacao = data.get("data_ultima_atualizacao", str(datetime.now()))
        except (FileNotFoundError, json.JSONDecodeError):
            self.salvar() # Cria um novo arquivo se ele não existir ou estiver corrompido

    def salvar(self):
        dados = {
            "saldo_atual": self.saldo_atual,
            "total_ganhos": self.total_ganhos,
            "total_perdas": self.total_perdas,
            "operacoes_ganhas": self.operacoes_ganhas,
            "operacoes_perdidas": self.operacoes_perdidas,
            "data_ultima_atualizacao": str(datetime.now())
        }
        with open(self.file_path, 'w') as f:
            json.dump(dados, f, indent=4)

    def registrar_resultado(self, resultado, stake_executada):
        payout = self.stake_base * 0.8
        if resultado == "win":
            lucro = payout
            self.total_ganhos += lucro
            self.saldo_atual += lucro
            self.operacoes_ganhas += 1
        elif resultado == "loss":
            perda = -stake_executada
            self.total_perdas += perda
            self.saldo_atual += perda
            self.operacoes_perdidas += 1
        
        self.salvar()

class PainelDesempenho:
    def __init__(self, saldo_inicial):
        print(f"💰 Painel de Desempenho iniciado. Saldo inicial: {saldo_inicial:.2f}")
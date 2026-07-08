import csv
import os
from datetime import datetime

class Logger:
    def __init__(self):
        # Caminhos de log
        self.dir = "logs"
        self.operacoes_csv = os.path.join(self.dir, "operacoes.csv")
        self.sistema_log = os.path.join(self.dir, "sistema.log")

        # Cria diretório se não existir
        if not os.path.exists(self.dir):
            os.makedirs(self.dir)

        # Inicializa CSV de operações
        if not os.path.exists(self.operacoes_csv):
            with open(self.operacoes_csv, mode="w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow([
                    "Data", "Tipo", "Preço", "RSI", "BB Inferior", "BB Superior", "Stake"
                ])

    def safe_round(self, value, digits=2):
        return round(value, digits) if value is not None else None

    def registrar_operacao(self, tipo, price, rsi, lower, upper, stake):
        """Registra operação em CSV"""
        with open(self.operacoes_csv, mode="a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([
                datetime.now().isoformat(sep=" ", timespec="seconds"),
                tipo,
                round(price, 2),
                self.safe_round(rsi),
                self.safe_round(lower),
                self.safe_round(upper),
                round(stake, 2)
            ])
    def registrar(self, direcao, preco, status, contract_id, resultado, stake):
        # Este método serve apenas para guardar o histórico da operação
        mensagem = f"OPERAÇÃO: {direcao} | PREÇO: {preco} | RESULTADO: {resultado} | STAKE: {stake}"
        self.log("INFO", mensagem)        

    def log(self, nivel, mensagem):
        """Registra mensagem em sistema.log"""
        linha = f"{datetime.now().isoformat(sep=' ', timespec='seconds')} [{nivel}] {mensagem}"
        print(linha)  # continua mostrando no terminal
        with open(self.sistema_log, mode="a", encoding="utf-8") as file:
            file.write(linha + "\n")

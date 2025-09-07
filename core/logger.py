import csv
import os
from datetime import datetime

class Logger:
    def __init__(self):
        self.caminho = "logs/operacoes.csv"
        if not os.path.exists("logs"):
            os.makedirs("logs")
        if not os.path.exists(self.caminho):
            with open(self.caminho, mode="w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["Data", "Tipo", "Preço", "RSI", "BB Inferior", "BB Superior", "Stake"])

    def registrar(self, tipo, price, rsi, lower, upper, stake):
        with open(self.caminho, mode="a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                tipo,
                round(price, 2),
                round(rsi, 2),
                round(lower, 2),
                round(upper, 2),
                round(stake, 2)
            ])
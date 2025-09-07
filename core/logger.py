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

    def safe_round(self, value, digits=2):
        return round(value, digits) if value is not None else None

    def registrar(self, tipo, price, rsi, lower, upper, stake):
        with open(self.caminho, mode="a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                tipo,
                round(price, 2),
                self.safe_round(rsi),
                self.safe_round(lower),
                self.safe_round(upper),
                round(stake, 2)
            ])
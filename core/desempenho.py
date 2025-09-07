import csv
from datetime import datetime

class PainelDesempenho:
    def __init__(self, saldo_inicial):
        self.saldo_inicial = saldo_inicial
        self.arquivo = f"logs/desempenho_{datetime.now().date()}.csv"
        self._iniciar_csv()

    def _iniciar_csv(self):
        with open(self.arquivo, mode="w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Hora", "Saldo", "Lucro", "Resultado", "Stake", "Tipo"])

    def registrar_operacao(self, saldo_atual, resultado, stake, tipo):
        lucro = round(saldo_atual - self.saldo_inicial, 2)
        hora = datetime.now().strftime("%H:%M:%S")
        with open(self.arquivo, mode="a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([hora, saldo_atual, lucro, resultado, stake, tipo])
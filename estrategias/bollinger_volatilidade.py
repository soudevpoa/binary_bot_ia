import numpy as np

class EstrategiaBollingerVolatilidade:
    def __init__(self, periodo=20, desvio=2, limiar_volatilidade=0.5):
        self.periodo = periodo
        self.desvio = desvio
        self.limiar_volatilidade = limiar_volatilidade

    def decidir(self, prices):
        if len(prices) < self.periodo:
            return None, None, None, None, "dados_insuficientes"

        media = np.mean(prices[-self.periodo:])
        std = np.std(prices[-self.periodo:])
        upper = media + self.desvio * std
        lower = media - self.desvio * std
        price = prices[-1]

        volatilidade = std / media  # Volatilidade relativa

        if price > upper and volatilidade > self.limiar_volatilidade:
            return "PUT", price, lower, upper, "rompimento_superior"
        elif price < lower and volatilidade > self.limiar_volatilidade:
            return "CALL", price, lower, upper, "rompimento_inferior"

        return None, price, lower, upper, "neutro"
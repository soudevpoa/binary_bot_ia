import numpy as np

class EstrategiaRSI:
    def __init__(self, rsi_period=14, bollinger_period=20, desvio=2):
        self.rsi_period = rsi_period
        self.bollinger_period = bollinger_period
        self.desvio = desvio

    def calcular_rsi(self, prices):
        if len(prices) < self.rsi_period + 1:
            return None

        diffs = np.diff(prices[-(self.rsi_period + 1):])
        ganhos = np.where(diffs > 0, diffs, 0)
        perdas = np.where(diffs < 0, -diffs, 0)

        media_ganhos = np.mean(ganhos)
        media_perdas = np.mean(perdas)

        if media_perdas == 0:
            return 100.0

        rs = media_ganhos / media_perdas
        rsi = 100 - (100 / (1 + rs))
        return round(rsi, 2)

    def calcular_bollinger(self, prices):
        if len(prices) < self.bollinger_period:
            return None, None

        media = np.mean(prices[-self.bollinger_period:])
        std = np.std(prices[-self.bollinger_period:])
        upper = media + self.desvio * std
        lower = media - self.desvio * std
        return round(lower, 2), round(upper, 2)

    def decidir(self, prices, volatilidade=None, limiar_dinamico=None):
        if len(prices) < max(self.rsi_period + 1, self.bollinger_period):
            return None, None, None, None, "dados_insuficientes"

        rsi = self.calcular_rsi(prices)
        lower, upper = self.calcular_bollinger(prices)
        price = prices[-1]

        if rsi is None or lower is None or upper is None:
            return None, rsi, lower, upper, "dados_insuficientes"

        if rsi < 30 and price < lower:
            return "CALL", rsi, lower, upper, "sobrevendido_rompimento_inferior"
        elif rsi > 70 and price > upper:
            return "PUT", rsi, lower, upper, "sobrecomprado_rompimento_superior"

        return None, rsi, lower, upper, "neutro"
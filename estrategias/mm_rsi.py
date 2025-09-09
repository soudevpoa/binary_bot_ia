import numpy as np

class EstrategiaMMRSI:
    def __init__(self, mm_curto=5, mm_longo=20, rsi_period=14, rsi_upper=70, rsi_lower=30):
        self.mm_curto = mm_curto
        self.mm_longo = mm_longo
        self.rsi_period = rsi_period
        self.rsi_upper = rsi_upper
        self.rsi_lower = rsi_lower
        self.ultima_direcao = None

    def calcular_media(self, prices, periodo):
        if len(prices) < periodo:
            return None
        return np.mean(prices[-periodo:])

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

    def decidir(self, prices, volatilidade, limiar_volatilidade):
        if volatilidade < limiar_volatilidade:
            return None, None, None, None, "Volatilidade insuficiente"

        if len(prices) < self.rsi_period:
            return None, None, None, None, "dados_insuficientes"

        rsi = self.calcular_rsi(prices)
        media = self.calcular_media(prices, self.mm_longo)
        price = prices[-1]

        if rsi is None or media is None:
            return None, None, None, None, "indicadores_indisponiveis"

        if rsi > self.rsi_upper and price > media:
            return "PUT", rsi, media, price, "sobrecompra"
        elif rsi < self.rsi_lower and price < media:
            return "CALL", rsi, media, price, "sobrevenda"

        return None, rsi, media, price, "neutro"
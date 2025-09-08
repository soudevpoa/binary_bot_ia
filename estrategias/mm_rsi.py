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

    def decidir(self, prices):
        if len(prices) < max(self.mm_curto, self.mm_longo, self.rsi_period + 1):
            return None, None, None, None, "dados_insuficientes"

        ma_curta = self.calcular_media(prices, self.mm_curto)
        ma_longa = self.calcular_media(prices, self.mm_longo)
        rsi = self.calcular_rsi(prices)
        price = prices[-1]

        print(f"🔍 MM Curta: {ma_curta:.2f} | MM Longa: {ma_longa:.2f} | RSI: {rsi}")

        if ma_curta > ma_longa and rsi < self.rsi_lower and self.ultima_direcao != "alta":
            self.ultima_direcao = "alta"
            return "CALL", rsi, ma_curta, ma_longa, "mm_rsi_alta"

        elif ma_curta < ma_longa and rsi > self.rsi_upper and self.ultima_direcao != "baixa":
            self.ultima_direcao = "baixa"
            return "PUT", rsi, ma_curta, ma_longa, "mm_rsi_baixa"

        return None, rsi, ma_curta, ma_longa, "neutro"
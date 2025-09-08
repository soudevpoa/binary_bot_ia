import numpy as np

class EstrategiaMediaMovel:
    def __init__(self, periodo_curto=5, periodo_longo=20):
        self.periodo_curto = periodo_curto
        self.periodo_longo = periodo_longo
        self.ultima_direcao = None

    def calcular_media(self, prices, periodo):
        if len(prices) < periodo:
            return None
        return np.mean(prices[-periodo:])

    def decidir(self, prices):
        if len(prices) < max(self.periodo_curto, self.periodo_longo):
            return None, None, None, None, "dados_insuficientes"

        ma_curta = self.calcular_media(prices, self.periodo_curto)
        ma_longa = self.calcular_media(prices, self.periodo_longo)
        price = prices[-1]

        if ma_curta > ma_longa and self.ultima_direcao != "alta":
            self.ultima_direcao = "alta"
            return "CALL", price, ma_curta, ma_longa, "cruzamento_alta"

        elif ma_curta < ma_longa and self.ultima_direcao != "baixa":
            self.ultima_direcao = "baixa"
            return "PUT", price, ma_curta, ma_longa, "cruzamento_baixa"

        return None, price, ma_curta, ma_longa, "neutro"
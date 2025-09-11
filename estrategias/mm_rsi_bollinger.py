import numpy as np

class EstrategiaMMRSIBollinger:
    def __init__(self, mm_curto=5, mm_longo=20, rsi_period=14,
                 rsi_upper=70, rsi_lower=30, bollinger_period=20, desvio=2):
        self.mm_curto = mm_curto
        self.mm_longo = mm_longo
        self.rsi_period = rsi_period
        self.rsi_upper = rsi_upper
        self.rsi_lower = rsi_lower
        self.bollinger_period = bollinger_period
        self.desvio = desvio
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

    def calcular_bollinger(self, prices):
        if len(prices) < self.bollinger_period:
            return None, None
        media = np.mean(prices[-self.bollinger_period:])
        std = np.std(prices[-self.bollinger_period:])
        upper = media + self.desvio * std
        lower = media - self.desvio * std
        return round(lower, 2), round(upper, 2)

    def decidir(self, prices, volatilidade=None, limiar_dinamico=None):
        # Checa dados mínimos
        if len(prices) < max(self.mm_curto, self.mm_longo, self.rsi_period + 1, self.bollinger_period):
            print("⚠️ Dados insuficientes para MM+RSI+Bollinger")
            return None, None, None, None, "dados_insuficientes"

        # Calcula indicadores
        ma_curta = self.calcular_media(prices, self.mm_curto)
        ma_longa = self.calcular_media(prices, self.mm_longo)
        rsi = self.calcular_rsi(prices)
        lower, upper = self.calcular_bollinger(prices)
        price = prices[-1]

        # Logs seguros
        vol_str = f"{volatilidade:.4f}" if volatilidade is not None else "N/A"
        limiar_str = f"{limiar_dinamico:.4f}" if limiar_dinamico is not None else "N/A"
        ma_curta_str = f"{ma_curta:.2f}" if ma_curta is not None else "N/A"
        ma_longa_str = f"{ma_longa:.2f}" if ma_longa is not None else "N/A"
        rsi_str = f"{rsi:.2f}" if rsi is not None else "N/A"
        lower_str = f"{lower:.2f}" if lower is not None else "N/A"
        upper_str = f"{upper:.2f}" if upper is not None else "N/A"

        print(f"📊 Volatilidade: {vol_str} | Limiar: {limiar_str}")
        print(f"🔍 MM Curta: {ma_curta_str} | MM Longa: {ma_longa_str} | RSI: {rsi_str} | Bollinger: [{lower_str}, {upper_str}]")

        # Se algum indicador não foi calculado
        if None in (ma_curta, ma_longa, rsi, lower, upper):
            return None, rsi, lower, upper, "indicadores_indisponiveis"

        # Condição de compra (CALL)
        if ma_curta > ma_longa and rsi < self.rsi_lower and price < lower and self.ultima_direcao != "alta":
            self.ultima_direcao = "alta"
            print("🔺 Sinal de alta confirmado por MM+RSI+Bollinger")
            return "CALL", rsi, lower, upper, "mm_rsi_bollinger_alta"

        # Condição de venda (PUT)
        elif ma_curta < ma_longa and rsi > self.rsi_upper and price > upper and self.ultima_direcao != "baixa":
            self.ultima_direcao = "baixa"
            print("🔻 Sinal de baixa confirmado por MM+RSI+Bollinger")
            return "PUT", rsi, lower, upper, "mm_rsi_bollinger_baixa"

        print("⏸️ Nenhuma condição atendida → Neutro")
        return None, rsi, lower, upper, "neutro"

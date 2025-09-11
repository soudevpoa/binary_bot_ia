import numpy as np

class EstrategiaRSI:
    def __init__(self, rsi_period=14, bollinger_period=20, desvio=2,
                 nivel_sobrevenda=30, nivel_sobrecompra=70):
        self.rsi_period = rsi_period
        self.bollinger_period = bollinger_period
        self.desvio = desvio
        self.nivel_sobrevenda = nivel_sobrevenda
        self.nivel_sobrecompra = nivel_sobrecompra

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
        if len(prices) < max(self.rsi_period + 1, self.bollinger_period):
            print("⚠️ Dados insuficientes para RSI/Bollinger")
            return None, None, None, None, "dados_insuficientes"

        # Calcula indicadores
        rsi = self.calcular_rsi(prices)
        lower, upper = self.calcular_bollinger(prices)
        price = prices[-1]

        # Log seguro
        vol_str = f"{volatilidade:.4f}" if volatilidade is not None else "N/A"
        limiar_str = f"{limiar_dinamico:.4f}" if limiar_dinamico is not None else "N/A"
        print(f"📊 Volatilidade: {vol_str} | Limiar: {limiar_str}")
        print(f"📈 RSI: {rsi if rsi is not None else 'N/A'} | Preço: {price:.2f} | "
              f"Banda Inferior: {lower if lower is not None else 'N/A'} | "
              f"Banda Superior: {upper if upper is not None else 'N/A'}")

        # Se algum indicador não foi calculado
        if rsi is None or lower is None or upper is None:
            return None, rsi, lower, upper, "dados_insuficientes"

        # Condições de entrada
        if rsi < self.nivel_sobrevenda and price < lower:
            print("🔺 Sinal de compra (sobrevendido + rompimento inferior)")
            return "CALL", rsi, lower, upper, "sobrevendido_rompimento_inferior"

        elif rsi > self.nivel_sobrecompra and price > upper:
            print("🔻 Sinal de venda (sobrecomprado + rompimento superior)")
            return "PUT", rsi, lower, upper, "sobrecomprado_rompimento_superior"

        # Neutro
        print("⏸️ Nenhuma condição atendida → Neutro")
        return None, rsi, lower, upper, "neutro"

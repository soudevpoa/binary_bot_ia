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
        print(f"📊 Volatilidade atual: {volatilidade:.4f} | Limiar: {limiar_volatilidade:.4f}")
        print(f"📉 Últimos preços: {prices[-5:]}")

        if volatilidade < limiar_volatilidade:
            print("⚠️ Volatilidade insuficiente")
            return None, None, None, None, "Volatilidade insuficiente"

        if len(prices) < self.rsi_period + 1:
            print("⚠️ Dados insuficientes para RSI")
            return None, None, None, None, "dados_insuficientes"

        rsi = self.calcular_rsi(prices)
        media = self.calcular_media(prices, self.mm_longo)
        price = prices[-1] if prices else None

        media_str = f"{media:.5f}" if media is not None else "N/A"
        price_str = f"{price:.5f}" if price is not None else "N/A"
        print(f"📈 RSI: {rsi} | Média Móvel Longa: {media_str} | Preço atual: {price_str}")

        if rsi is None or media is None:
            print("⚠️ Indicadores indisponíveis")
            return None, None, None, None, "indicadores_indisponiveis"

        # 🔧 RSI adaptativo baseado na volatilidade
        rsi_upper_adaptado = min(self.rsi_upper + (volatilidade * 10), 90)
        rsi_lower_adaptado = max(self.rsi_lower - (volatilidade * 10), 10)
        print(f"🎛️ RSI adaptado: upper={rsi_upper_adaptado:.2f} | lower={rsi_lower_adaptado:.2f}")

        # 🔍 Confirmação com candle
        open_price = prices[-2] if len(prices) >= 2 else None
        close_price = prices[-1] if prices else None

        if rsi > rsi_upper_adaptado and price > media:
            if open_price is not None and close_price is not None and close_price < open_price:
                print("🔻 PUT confirmado por candle de baixa")
                return "PUT", rsi, media, price, "sobrecompra_confirmada"
            else:
                print("⚠️ PUT técnico detectado, mas candle não confirmou")

        elif rsi < rsi_lower_adaptado and price < media:
            if open_price is not None and close_price is not None and close_price > open_price:
                print("🔺 CALL confirmado por candle de alta")
                return "CALL", rsi, media, price, "sobrevenda_confirmada"
            else:
                print("⚠️ CALL técnico detectado, mas candle não confirmou")

        print("⏸️ Nenhuma condição atendida → Neutro")
        return None, rsi, media, price, "neutro"
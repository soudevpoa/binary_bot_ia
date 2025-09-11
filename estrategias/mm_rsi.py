import numpy as np

class EstrategiaMMRSI:
    def __init__(self, mm_curto=5, mm_longo=20, rsi_period=14,
                 rsi_upper=70, rsi_lower=30):
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

    def decidir(self, prices, volatilidade=None, limiar_volatilidade=None):
        # Logs iniciais
        vol_str = f"{volatilidade:.4f}" if volatilidade is not None else "N/A"
        limiar_str = f"{limiar_volatilidade:.4f}" if limiar_volatilidade is not None else "N/A"
        print(f"📊 Volatilidade atual: {vol_str} | Limiar: {limiar_str}")
        print(f"📉 Últimos preços: {prices[-5:]}")

        # Filtro de volatilidade
        if volatilidade is not None and limiar_volatilidade is not None:
            if volatilidade < limiar_volatilidade:
                print("⚠️ Volatilidade insuficiente")
                return None, "volatilidade_insuficiente"

        # Dados mínimos para RSI
        if len(prices) < self.rsi_period + 1:
            print("⚠️ Dados insuficientes para RSI")
            return None, "dados_insuficientes"

        # Calcula indicadores
        rsi = self.calcular_rsi(prices)
        media = self.calcular_media(prices, self.mm_longo)
        price = prices[-1] if prices else None

        rsi_str = f"{rsi:.2f}" if rsi is not None else "N/A"
        media_str = f"{media:.5f}" if media is not None else "N/A"
        price_str = f"{price:.5f}" if price is not None else "N/A"
        print(f"📈 RSI: {rsi_str} | Média Móvel Longa: {media_str} | Preço atual: {price_str}")

        if rsi is None or media is None:
            print("⚠️ Indicadores indisponíveis")
            return None, "indicadores_indisponiveis"

        # Adaptação dinâmica do RSI
        rsi_upper_adaptado = min(self.rsi_upper + (volatilidade * 10 if volatilidade else 0), 90)
        rsi_lower_adaptado = max(self.rsi_lower - (volatilidade * 10 if volatilidade else 0), 10)
        print(f"🎛️ RSI adaptado: upper={rsi_upper_adaptado:.2f} | lower={rsi_lower_adaptado:.2f}")

        open_price = prices[-2] if len(prices) >= 2 else None
        close_price = prices[-1] if prices else None

        # Condição de venda (PUT)
        if rsi > rsi_upper_adaptado and price > media:
            if open_price is not None and close_price is not None and close_price < open_price:
                if self.ultima_direcao != "baixa":
                    self.ultima_direcao = "baixa"
                    print("🔻 PUT confirmado por candle de baixa")
                    return "PUT", "sobrecompra_confirmada"
            else:
                print("⚠️ PUT técnico detectado, mas candle não confirmou")

        # Condição de compra (CALL)
        elif rsi < rsi_lower_adaptado and price < media:
            if open_price is not None and close_price is not None and close_price > open_price:
                if self.ultima_direcao != "alta":
                    self.ultima_direcao = "alta"
                    print("🔺 CALL confirmado por candle de alta")
                    return "CALL", "sobrevenda_confirmada"
            else:
                print("⚠️ CALL técnico detectado, mas candle não confirmou")

        print("⏸️ Nenhuma condição atendida → Neutro")
        return None, "neutro"

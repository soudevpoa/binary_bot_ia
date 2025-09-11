import numpy as np

class EstrategiaReversaoTendencia:
    def __init__(self, rsi_period=14, nivel_sobrevenda=30, nivel_sobrecompra=70):
        self.rsi_period = rsi_period
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

    def detectar_reversao(self, prices):
        if len(prices) < self.rsi_period + 2:
            return None, "dados_insuficientes"
        rsi = self.calcular_rsi(prices)
        atual = prices[-1]
        anterior = prices[-2]
        if rsi is not None:
            if rsi < self.nivel_sobrevenda and atual > anterior:
                return "CALL", "rsi_baixo_reversao_alta"
            if rsi > self.nivel_sobrecompra and atual < anterior:
                return "PUT", "rsi_alto_reversao_baixa"
        return None, "neutro"
    
    def detectar_candle_exaustao(self, candles):
        if not candles:
            return None
        ultimo = candles[-1]
        open_ = ultimo.get("open")
        close = ultimo.get("close")
        high = ultimo.get("high")
        low = ultimo.get("low")
        if None in (open_, close, high, low):
            return None

        corpo = abs(close - open_)
        sombra_superior = high - max(close, open_)
        sombra_inferior = min(close, open_) - low

        if corpo < sombra_inferior * 0.5 and sombra_inferior > sombra_superior:
            return "martelo"
        elif corpo < sombra_superior * 0.5 and sombra_superior > sombra_inferior:
            return "estrela_cadente"
        return None

    def gerar_candles(self, prices):
        candles = []
        for i in range(len(prices) - 1):
            candles.append({
                "open": prices[i],
                "close": prices[i + 1],
                "high": max(prices[i], prices[i + 1]),
                "low": min(prices[i], prices[i + 1])
            })
        return candles

    def decidir(self, prices, volatilidade=None, limiar_dinamico=None):
        if len(prices) < self.rsi_period + 2:
            print("⚠️ Dados insuficientes para reversão de tendência")
            return None, "dados_insuficientes"

        rsi = self.calcular_rsi(prices)
        tipo, padrao_rsi = self.detectar_reversao(prices)
        candles = self.gerar_candles(prices)
        padrao_candle = self.detectar_candle_exaustao(candles)

        vol_str = f"{volatilidade:.4f}" if volatilidade is not None else "N/A"
        limiar_str = f"{limiar_dinamico:.4f}" if limiar_dinamico is not None else "N/A"
        print(f"📊 Volatilidade: {vol_str} | Limiar: {limiar_str}")
        print(f"🔍 RSI: {rsi if rsi is not None else 'N/A'} | Candle: {padrao_candle} | Tipo RSI: {tipo}")

        # Confirmação dupla RSI + Candle
        if tipo and padrao_candle:
            padrao_combinado = f"{padrao_rsi}+{padrao_candle}"
            print(f"✅ Confirmação dupla detectada: {padrao_combinado}")
            return tipo, padrao_combinado

        # Apenas candle com suporte do RSI
        if padrao_candle and not tipo:
            if rsi is not None and rsi < self.nivel_sobrevenda and padrao_candle == "martelo":
                return "CALL", padrao_candle
            elif rsi is not None and rsi > self.nivel_sobrecompra and padrao_candle == "estrela_cadente":
                return "PUT", padrao_candle

        # Apenas RSI ou neutro
        return tipo, padrao_rsi or "neutro"

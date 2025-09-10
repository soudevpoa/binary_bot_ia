import numpy as np

class EstrategiaReversaoTendencia:
    def __init__(self, rsi_period=14):
        self.rsi_period = rsi_period

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

        if rsi < 30 and atual > anterior:
            return "CALL", "rsi_baixo_reversao_alta"
        if rsi > 70 and atual < anterior:
            return "PUT", "rsi_alto_reversao_baixa"

        return None, "neutro"
    
    def detectar_candle_exaustao(self, candles):
        if len(candles) < 1:
            return None

        ultimo = candles[-1]
        corpo = abs(ultimo["close"] - ultimo["open"])
        sombra_superior = ultimo["high"] - max(ultimo["close"], ultimo["open"])
        sombra_inferior = min(ultimo["close"], ultimo["open"]) - ultimo["low"]

        if corpo < sombra_inferior * 0.5 and sombra_inferior > sombra_superior:
            return "martelo"
        elif corpo < sombra_superior * 0.5 and sombra_superior > sombra_inferior:
            return "estrela_cadente"
        return None

    def gerar_candles(self, prices):
        candles = []
        for i in range(len(prices) - 1):
            candle = {
                "open": prices[i],
                "close": prices[i + 1],
                "high": max(prices[i], prices[i + 1]),
                "low": min(prices[i], prices[i + 1])
            }
            candles.append(candle)
        return candles

    def decidir(self, prices, volatilidade=None, limiar_dinamico=None):
        rsi = self.calcular_rsi(prices)
        tipo, padrao_rsi = self.detectar_reversao(prices)
        candles = self.gerar_candles(prices)
        padrao_candle = self.detectar_candle_exaustao(candles)
        
        print(f"🔍 RSI: {rsi} | Candle: {padrao_candle} | Tipo: {tipo}")

        lower, upper = None, None

        if tipo and padrao_candle:
            padrao_combinado = f"{padrao_rsi}+{padrao_candle}"
            return tipo, rsi, lower, upper, padrao_combinado

        if padrao_candle and not tipo:
            if rsi and rsi < 30 and padrao_candle == "martelo":
                return "CALL", rsi, lower, upper, padrao_candle
            elif rsi and rsi > 70 and padrao_candle == "estrela_cadente":
                return "PUT", rsi, lower, upper, padrao_candle

        return tipo, rsi, lower, upper, padrao_rsi or "neutro"
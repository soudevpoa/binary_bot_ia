class EstrategiaPriceAction:
    def __init__(self):
        pass

    def decidir(self, candles):
        if len(candles) < 3:
            return None, "dados_insuficientes"

        penultimo = candles[-2]
        ultimo = candles[-1]

        # Engolfo de alta
        if penultimo["close"] < penultimo["open"] and ultimo["close"] > ultimo["open"]:
            if ultimo["open"] < penultimo["close"] and ultimo["close"] > penultimo["open"]:
                return "CALL", "engolfo_alta"

        # Engolfo de baixa
        if penultimo["close"] > penultimo["open"] and ultimo["close"] < ultimo["open"]:
            if ultimo["open"] > penultimo["close"] and ultimo["close"] < penultimo["open"]:
                return "PUT", "engolfo_baixa"

        # Martelo
        if self._eh_martelo(ultimo):
            return "CALL", "martelo"

        # Estrela da manhã
        if self._eh_estrela_da_manha(candles):
            return "CALL", "estrela_da_manha"

        return None, "neutro"

    def _eh_martelo(self, candle):
        corpo = abs(candle["close"] - candle["open"])
        sombra_inferior = min(candle["open"], candle["close"]) - candle["low"]
        sombra_superior = candle["high"] - max(candle["open"], candle["close"])
        return sombra_inferior > corpo * 2 and sombra_superior < corpo * 0.5

    def _eh_estrela_da_manha(self, candles):
        c1, c2, c3 = candles[-3], candles[-2], candles[-1]
        corpo1 = abs(c1["close"] - c1["open"])
        corpo2 = abs(c2["close"] - c2["open"])
        corpo3 = abs(c3["close"] - c3["open"])

        cond1 = c1["close"] < c1["open"] and corpo1 > corpo2
        cond2 = corpo2 < corpo1 * 0.5
        cond3 = c3["close"] > c3["open"] and c3["close"] > (c1["open"] + c1["close"]) / 2

        return cond1 and cond2 and cond3
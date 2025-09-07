class EstrategiaPriceAction:
    def decidir(self, candles):
        if len(candles) < 2:
            return None, None, None, None, "dados_insuficientes"

        ultimo = candles[-1]
        anterior = candles[-2]

        # Exemplo: Engolfo de alta
        if anterior["close"] < anterior["open"] and ultimo["close"] > ultimo["open"] and ultimo["close"] > anterior["open"]:
            return "CALL", None, None, None, "engolfo_alta"

        # Exemplo: Engolfo de baixa
        if anterior["close"] > anterior["open"] and ultimo["close"] < ultimo["open"] and ultimo["close"] < anterior["open"]:
            return "PUT", None, None, None, "engolfo_baixa"

        return None, None, None, None, "neutro"
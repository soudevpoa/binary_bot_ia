class EstrategiaPriceAction:
    def __init__(self):
        pass

    def decidir(self, candles):
        if len(candles) < 2:
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

        return None, "neutro"
class EstrategiaRSI:
    def __init__(self, rsi_period, bollinger_period):
        self.rsi_period = rsi_period
        self.bollinger_period = bollinger_period

    def decidir(self, prices):
        # Simples lógica de RSI + Bollinger
        rsi = self._calcular_rsi(prices)
        lower, upper = self._calcular_bollinger(prices)

        if rsi < 30 and prices[-1] < lower:
            return "CALL", rsi, lower, upper
        elif rsi > 70 and prices[-1] > upper:
            return "PUT", rsi, lower, upper
        return None, rsi, lower, upper

    def _calcular_rsi(self, prices):
        # Lógica simplificada
        return 50  # Simulação

    def _calcular_bollinger(self, prices):
        # Lógica simplificada
        return prices[-1] - 1, prices[-1] + 1
from indicadores.indicadores import calcular_rsi, calcular_bb

class Estrategia:
    def __init__(self, rsi_period, bb_period):
        self.rsi_period = rsi_period
        self.bb_period = bb_period

    
    def decidir(self, prices):
        rsi = calcular_rsi(prices[-self.bb_period:], self.rsi_period)
        lower, upper = calcular_bb(prices[-self.bb_period:], self.bb_period)

        if rsi < 30 and prices[-1] < lower:
            return "CALL", rsi, lower, upper
        elif rsi > 70 and prices[-1] > upper:
            return "PUT", rsi, lower, upper
        else:
            return None, rsi, lower, upper
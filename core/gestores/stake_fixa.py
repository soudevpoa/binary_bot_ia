class StakeFixa:
    def __init__(self, valor):
        if valor <= 0:
            raise ValueError("Stake fixa deve ser > 0.")
        self.valor = float(valor)

    def get_stake(self):
        return round(self.valor, 2)

    def registrar_resultado(self, resultado, payout=None, stake_executada=None):
        # Stake fixa não muda
        pass

    def resetar(self):
        pass

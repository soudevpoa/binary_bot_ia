class MartingaleTradicional:
    def __init__(self, stake_base=1.0, fator=2, limite=3):
        self.stake_base = stake_base
        self.fator = fator
        self.limite = limite
        self.contador = 0

    def get_stake(self):
        return round(self.stake_base * (self.fator ** self.contador), 2)

    def registrar_resultado(self, resultado, payout=None, stake_executada=None):
        if resultado == "loss":
            self.contador += 1
            if self.contador >= self.limite:
                self.contador = 0
        else:
            self.contador = 0

    def resetar(self):
        self.contador = 0

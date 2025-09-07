class MartingaleInteligente:
    def __init__(self, stake_base, max_niveis=3, fator_multiplicador=2):
        self.stake_base = stake_base
        self.stake_atual = stake_base
        self.nivel = 0
        self.max_niveis = max_niveis
        self.fator = fator_multiplicador

    def registrar_resultado(self, resultado):
        if resultado == "loss":
            if self.nivel < self.max_niveis:
                self.nivel += 1
                self.stake_atual *= self.fator
            else:
                # Reseta após atingir o limite
                self.nivel = 0
                self.stake_atual = self.stake_base
        elif resultado == "win":
            # Reseta após vitória
            self.nivel = 0
            self.stake_atual = self.stake_base

    def get_stake(self):
        return round(self.stake_atual, 2)

    def reduzir_stake(self, fator=0.5):
        self.stake_atual *= fator
        self.stake_atual = max(self.stake_atual, self.stake_base)
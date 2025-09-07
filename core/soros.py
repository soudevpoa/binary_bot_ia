class GerenciadorSoros:
    def __init__(self, stake_base, max_etapas=2):
        self.stake_base = stake_base
        self.stake_atual = stake_base
        self.etapa = 1
        self.max_etapas = max_etapas
        self.ativo = True

    def registrar_resultado(self, resultado):
     if resultado == "win":
        if self.etapa < self.max_etapas:
            self.stake_atual *= 2
            self.etapa += 1
        else:
            self.resetar()
     elif resultado == "loss":
        self.stake_atual *= 2
        self.etapa = 1

     else:
            self.resetar()
            print(f"🔁 SorosGale atualizado | Etapa: {self.etapa} | Nova stake: {self.stake_atual}")

    def resetar(self):
        self.stake_atual = self.stake_base
        self.etapa = 1
    
    def reduzir_stake(self, fator=0.5):
        self.stake_atual = max(round(self.stake_atual * fator, 2), 0.35)
        self.etapa = 0


    def get_stake(self, saldo=None):
        if saldo is not None:
            if saldo < 20:
                return 0.35
        elif saldo < 100:
            return round(saldo * 0.01, 2)
        else:
            return round(saldo * 0.02, 2)
        return max(round(self.stake_atual, 2), 0.35)
    
    def calcular_stake_recuperacao(self, prejuizo_total, payout):
        stake = round(prejuizo_total / payout, 2)
        return max(stake, 0.35)

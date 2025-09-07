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

    def get_stake(self, saldo):
        if saldo < 20:
            return 0.35
        elif saldo < 100:
            return round(saldo * 0.01, 2)
        else:
            return round(saldo * 0.02, 2)

class Soros:
    def __init__(self, stake_base, max_etapas=2, stake_max=None, reinvestir="lucro"):
        self.stake_base = float(stake_base)
        self.stake_atual = float(stake_base)
        self.etapa = 1
        self.max_etapas = max_etapas
        self.stake_max = stake_max
        self.reinvestir = reinvestir  # "lucro" ou "payout"
        self.lucro_acumulado = 0.0

    def registrar_resultado(self, resultado, payout=None, stake_executada=None):
        if resultado not in ("win", "loss"):
            return

        if resultado == "loss":
            self.resetar()
            print("📉 Soros resetado por perda.")
            return

        # Vitória
        if payout is None or stake_executada is None:
            self.resetar()
            print("ℹ️ Soros sem payout/stake → reset para stake_base.")
            return

        lucro = float(payout) - float(stake_executada)
        self.lucro_acumulado += max(lucro, 0.0)

        if self.reinvestir == "payout":
            proxima = float(payout)
        else:  # "lucro"
            proxima = self.stake_base + self.lucro_acumulado

        self.etapa += 1
        if self.etapa > self.max_etapas:
            print(f"🏁 Ciclo Soros concluído (níveis: {self.max_etapas}). Realizando lucro.")
            self.resetar()
            return

        if self.stake_max:
            proxima = min(proxima, self.stake_max)

        self.stake_atual = max(proxima, self.stake_base)
        print(f"🏆 Soros vitória. Etapa: {self.etapa} | Próxima stake: {self.stake_atual:.2f}")

    def get_stake(self, saldo=None):
        return round(self.stake_atual, 2)

    def reduzir_stake(self, fator=0.5):
        if fator <= 0:
            raise ValueError("O fator de redução deve ser > 0.")
        self.stake_atual *= fator
        self.stake_atual = max(self.stake_atual, self.stake_base)
        print(f"🔽 Stake Soros reduzida para {self.stake_atual:.2f}")

    def resetar(self):
        self.etapa = 1
        self.stake_atual = self.stake_base
        self.lucro_acumulado = 0.0

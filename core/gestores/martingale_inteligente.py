class MartingaleInteligente:
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
            print(f"❌ Martingale perdeu. Etapa atual: {self.contador}")
            if self.contador >= self.limite:
                print("🔁 Martingale atingiu limite. Resetando.")
                self.contador = 0
        else:
            print("✅ Martingale venceu. Resetando para etapa 0.")
            self.contador = 0


    def resetar(self):
        self.contador = 0

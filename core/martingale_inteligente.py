import math

class MartingaleInteligente:
    def __init__(self, stake_base, fator=2.0, limite=3):
        self.stake_base = stake_base
        self.stake_atual = stake_base
        self.limite_etapas = limite
        self.etapa_atual = 1
        self.perdas_acumuladas = 0.0

    def get_stake(self):
        return round(self.stake_atual, 2)

    def registrar_resultado(self, resultado, payout=0.0, stake_executada=0.0):
        # Reinicia a sequência em caso de vitória
        if resultado == "win":
            self.stake_atual = self.stake_base
            self.etapa_atual = 1
            self.perdas_acumuladas = 0.0
            return
        
        # Aumenta a sequência em caso de perda
        if resultado == "loss":
            self.etapa_atual += 1
            self.perdas_acumuladas += stake_executada

            # Verifica se atingiu o limite de etapas
            if self.etapa_atual > self.limite_etapas:
                print("❌ Limite de Martingale Inteligente atingido. Reiniciando stake.")
                self.stake_atual = self.stake_base
                self.etapa_atual = 1
                self.perdas_acumuladas = 0.0
                return

            # Se o payout for 0, usa uma taxa de payout padrão (para evitar divisão por zero)
            payout_real = payout if payout > 0 else 1.85 

            # Calcula o stake necessário para recuperar perdas + um pequeno lucro
            profit_desejado = self.stake_base * 0.01
            stake_necessario = (self.perdas_acumuladas + profit_desejado) / (payout_real - 1)
            self.stake_atual = round(stake_necessario, 2)
            
            print(f"📈 Calculando Martingale Inteligente: Stake ajustado para {self.stake_atual:.2f}")

    def resetar(self):
        self.stake_atual = self.stake_base
        self.etapa_atual = 1
        self.perdas_acumuladas = 0.0
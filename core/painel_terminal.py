class PainelTerminal:
    def __init__(self, saldo_inicial):
        self.saldo = saldo_inicial

    def registrar_operacao(self, saldo_atual, resultado, stake, direcao):
        print(f"[TERMINAL] {resultado} | {direcao} | Stake: {stake:.2f} | Saldo: {saldo_atual:.2f}")

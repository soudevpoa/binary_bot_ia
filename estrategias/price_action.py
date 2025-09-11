import numpy as np

class EstrategiaPriceAction:
    def __init__(self, variacao_minima=0.0):
        self.ultimo_preco_alto = None
        self.ultimo_preco_baixo = None
        self.variacao_minima = variacao_minima  # filtro para evitar micro sinais

    def decidir(self, prices, volatilidade=None, limiar_dinamico=None):
        # Checa dados mínimos
        if len(prices) < 2:
            print("⚠️ Dados insuficientes para Price Action")
            return None, "dados_insuficientes"

        # Logs iniciais
        vol_str = f"{volatilidade:.4f}" if volatilidade is not None else "N/A"
        limiar_str = f"{limiar_dinamico:.4f}" if limiar_dinamico is not None else "N/A"
        print(f"📊 Volatilidade: {vol_str} | Limiar: {limiar_str}")
        print(f"📉 Últimos preços: {prices[-5:]}")

        price_anterior = prices[-2]
        price_atual = prices[-1]

        # Condição para CALL (tendência de alta)
        if price_atual > price_anterior + self.variacao_minima:
            if self.ultimo_preco_alto is None or price_atual > self.ultimo_preco_alto:
                self.ultimo_preco_alto = price_atual
                print("🔺 Novo topo detectado → CALL")
                return "CALL", "novo_topo"
            elif self.ultimo_preco_baixo is not None and self.ultimo_preco_baixo < price_atual < self.ultimo_preco_alto:
                return None, "neutro"
            elif self.ultimo_preco_baixo is None or price_atual < self.ultimo_preco_baixo:
                self.ultimo_preco_baixo = price_atual
                return None, "neutro"

        # Condição para PUT (tendência de baixa)
        elif price_atual < price_anterior - self.variacao_minima:
            if self.ultimo_preco_baixo is None or price_atual < self.ultimo_preco_baixo:
                self.ultimo_preco_baixo = price_atual
                print("🔻 Novo fundo detectado → PUT")
                return "PUT", "novo_fundo"
            elif self.ultimo_preco_alto is not None and self.ultimo_preco_baixo < price_atual < self.ultimo_preco_alto:
                return None, "neutro"
            elif self.ultimo_preco_alto is None or price_atual > self.ultimo_preco_alto:
                self.ultimo_preco_alto = price_atual
                return None, "neutro"

        print("⏸️ Nenhuma condição atendida → Neutro")
        return None, "neutro"

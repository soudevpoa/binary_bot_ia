import numpy as np

class EstrategiaMediaMovel:
    def __init__(self, periodo_curto=5, periodo_longo=20):
        self.periodo_curto = periodo_curto
        self.periodo_longo = periodo_longo
        self.ultima_direcao = None
        self.tipo = "media_movel"

    def calcular_media(self, prices, periodo):
        if len(prices) < periodo:
            return None
        return np.mean(prices[-periodo:])

    def decidir(self, prices, volatilidade=None, limiar_dinamico=None):
        # Impressão segura mesmo se volatilidade for None
        vol_str = f"{volatilidade:.4f}" if volatilidade is not None else "N/A"
        limiar_str = f"{limiar_dinamico:.4f}" if limiar_dinamico is not None else "N/A"
        print(f"📊 Volatilidade atual: {vol_str} | Limiar: {limiar_str}")
        print(f"📉 Últimos preços: {prices[-5:]}")

        # Se a volatilidade for baixa, não opera
        if volatilidade is not None and limiar_dinamico is not None:
            if volatilidade < limiar_dinamico:
                print("⚠️ Volatilidade insuficiente")
                return None, "volatilidade_baixa"

        # Garante que há dados suficientes
        if len(prices) < max(self.periodo_curto, self.periodo_longo):
            print("⚠️ Dados insuficientes para médias móveis")
            return None, "dados_insuficientes"

        ma_curta = self.calcular_media(prices, self.periodo_curto)
        ma_longa = self.calcular_media(prices, self.periodo_longo)
        price = prices[-1]

        # Proteção contra None
        if ma_curta is None or ma_longa is None:
            return None, "dados_insuficientes"

        print(f"📈 MA Curta: {ma_curta:.5f} | MA Longa: {ma_longa:.5f} | Preço: {price:.5f}")

        # Condição para compra (CALL)
        if ma_curta > ma_longa and self.ultima_direcao != "alta":
            self.ultima_direcao = "alta"
            print("🔺 Cruzamento de alta detectado")
            return "CALL", "cruzamento_alta"

        # Condição para venda (PUT)
        elif ma_curta < ma_longa and self.ultima_direcao != "baixa":
            self.ultima_direcao = "baixa"
            print("🔻 Cruzamento de baixa detectado")
            return "PUT", "cruzamento_baixa"

        # Reset se médias se igualarem
        elif ma_curta == ma_longa:
            self.ultima_direcao = None

        # Nenhuma condição atendida
        print("⏸️ Nenhuma condição atendida → Neutro")
        return None, "neutro"
    def __str__(self):
        return f"Média Móvel (Curto: {self.periodo_curto}, Longo: {self.periodo_longo})"

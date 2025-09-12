import asyncio
import json
import numpy as np
from datetime import datetime
from indicadores.indicadores import calcular_rsi, calcular_mm, calcular_bb, calcular_volatilidade
from core.modelo_neural import ModeloNeural
from core.bot_base import BotBase

# --- Classe de Estratégia Específica para o Megalodon ---
class EstrategiaMegalodon:
    def __init__(self):
        # A Estratégia Megalodon tem sua própria lógica de IA
        self.modelo = ModeloNeural()
        
    def _preparar_dados(self, prices, config):
        """Prepara os dados para o modelo de IA."""
        if len(prices) < config["mm_periodo_longo"]:
            return None
        
        rsi = calcular_rsi(prices)
        mm_curta = calcular_mm(prices, config["mm_periodo_curto"])
        mm_longa = calcular_mm(prices, config["mm_periodo_longo"])
        vol = calcular_volatilidade(prices)
        
        # O modelo precisa de um array numpy de 2D
        features = np.array([rsi, mm_curta, mm_longa, vol]).reshape(1, -1)
        return features

    def decidir(self, prices, volatilidade=None, limiar_volatilidade=None):
        """Método exigido por BotBase. Decisão com base na IA."""
        # A lógica de decisão da IA foi movida para cá
        features = self._preparar_dados(prices, self.config) # self.config é acessado via BotBase
        if features is None:
            return None, "neutro"
            
        previsao = self.modelo.prever(features)
        
        if previsao == "up":
            return "CALL", "megalodon_detectou_alta"
        elif previsao == "down":
            return "PUT", "megalodon_detectou_baixa"
        
        return None, "neutro"

    async def treinar_com_historico_mercado(self, num_ticks, mercado, config):
        """Coleta ticks do mercado e treina o modelo."""
        prices_data = []
        for _ in range(num_ticks):
            try:
                msg = await mercado.ws.recv()
                data = mercado.processar_tick(msg)
                if data:
                    prices_data.append(data["price"])
            except Exception as e:
                print(f"⚠️ Erro ao coletar ticks para treinamento: {e}")
                break

        features, labels = [], []
        periodo_min = max(config.get("mm_periodo_longo", 20), 14)
        
        for i in range(len(prices_data) - 1):
            subset = prices_data[:i+1]
            if len(subset) >= periodo_min:
                f = self._preparar_dados(subset, config)
                if f is not None:
                    features.append(f[0])
                    labels.append(1 if prices_data[i+1] > prices_data[i] else 0)

        if features:
            X = np.array(features)
            y = np.array(labels)
            self.modelo.treinar(X, y)
            print("✅ Treinamento concluído com dados do mercado.")
        else:
            print("❌ Dados insuficientes para treinamento.")


# --- Classe BotMegalodon ---
class BotMegalodon(BotBase):
    def __init__(self, config, token, estatisticas_file):
        # AQUI ESTÁ A CORREÇÃO PRINCIPAL: 
        # Instanciar a EstratégiaMegalodon e passá-la para a classe pai
        estrategia = EstrategiaMegalodon()
        super().__init__(config, token, estrategia, estatisticas_file)
        
        # Agora, a estratégia tem acesso à configuração via self.estrategia.config
        self.estrategia.config = self.config
        
        self.modo_simulacao = config.get("modo_simulacao", True)

    async def iniciar(self):
        await super().iniciar()

        if self.modo_simulacao:
            print("📚 Treinando rede neural com dados simulados...")
            # Chamamos o método de treinamento da estratégia, passando os objetos necessários
            await self.estrategia.treinar_com_historico_mercado(num_ticks=100, mercado=self.mercado, config=self.config)
        
        # O loop principal agora será tratado pela BotBase,
        # que vai chamar o método `decidir` da sua `EstrategiaMegalodon`
        
    def _decidir(self):
        # Este método não é mais necessário aqui, pois a decisão é feita na estratégia.
        # Ele será chamado automaticamente pelo BotBase.
        pass
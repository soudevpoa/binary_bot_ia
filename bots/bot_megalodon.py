import asyncio
import json
import numpy as np
from datetime import datetime
from indicadores.indicadores import calcular_rsi, calcular_mm, calcular_bb, calcular_volatilidade
from core.modelo_neural import ModeloNeural
from core.bot_base import BotBase  # Importação da classe base

# Funções auxiliares, caso existam, devem ser definidas aqui
# ...

class BotMegalodon(BotBase):
    def __init__(self, config, token, estatisticas_file):
        # Chama o construtor da classe pai (BotBase)
        # O Megalodon não tem uma "estratégia" de Média Móvel, mas a classe pai precisa do argumento.
        # Vamos passar None para indicar que a decisão é feita pela IA.
        super().__init__(config, token, None, estatisticas_file)
        
        # Atributos específicos do Megalodon
        self.modelo = ModeloNeural()
        self.modo_simulacao = config.get("modo_simulacao", True)

    def _preparar_dados(self, prices):
        """Prepara os dados para o modelo de IA."""
        if len(prices) < self.config["mm_periodo_longo"]:
            return None, None
        
        rsi = calcular_rsi(prices)
        mm_curta = calcular_mm(prices, self.config["mm_periodo_curto"])
        mm_longa = calcular_mm(prices, self.config["mm_periodo_longo"])
        vol = calcular_volatilidade(prices)
        
        features = np.array([rsi, mm_curta, mm_longa, vol]).reshape(1, -1)
        return features, [rsi, mm_curta, mm_longa, vol]

    def _decidir_com_ia(self, prices):
        """Decide a operação com base na IA."""
        features, _ = self._preparar_dados(prices)
        if features is None:
            return None, "neutro"
            
        previsao = self.modelo.prever(features)
        
        if previsao == "up":
            return "CALL", "megalodon_detectou_alta"
        elif previsao == "down":
            return "PUT", "megalodon_detectou_baixa"
        
        return None, "neutro"

    async def _treinar_com_historico_mercado(self, num_ticks=100):
        """Coleta ticks do mercado em tempo real e treina o modelo."""
        prices_data = []
        for _ in range(num_ticks):
            try:
                msg = await self.mercado.ws.recv()
                data = self.mercado.processar_tick(msg)
                if data:
                    prices_data.append(data["price"])
            except Exception as e:
                print(f"⚠️ Erro ao coletar ticks para treinamento: {e}")
                break

        features, labels = [], []
        periodo_min = max(self.config.get("mm_periodo_longo", 20), 14) # RSI period
        
        for i in range(len(prices_data) - 1):
            subset = prices_data[:i+1]
            if len(subset) >= periodo_min:
                f, _ = self._preparar_dados(subset)
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

    async def iniciar(self):
        # A chamada para iniciar() da classe pai já lida com a conexão, executor e logger.
        # Nós apenas adicionamos a lógica específica do Megalodon.
        await super().iniciar()

        # A partir daqui, a lógica de loop principal já é tratada por BotBase.
        # O método `decidir` da nossa classe `Estrategia` será chamado
        # A estratégia do Megalodon é a IA, não a Média Móvel.
        # Por isso, nós vamos modificar o loop principal para usar a nossa IA.
        
        # Desliga o loop do BotBase para usar o nosso
        print("Ajustando o loop principal para a lógica do Megalodon...")
        
        if self.modo_simulacao:
            print("📚 Treinando rede neural com dados simulados...")
            await self._treinar_com_historico_mercado(num_ticks=100)
            
        while True:
            try:
                msg = await self.mercado.ws.recv()
                data = self.mercado.processar_tick(msg)
                if not data:
                    continue

                self.prices.append(data["price"])
                if len(self.prices) > 60:
                    self.prices.pop(0)

                # Decisão com a IA
                tipo, padrao = self._decidir_com_ia(self.prices)
                
                if tipo is None:
                    #print("⏳ Sem sinal. Aguardando próximo tick...")
                    await asyncio.sleep(1) # Espera um pouco para não sobrecarregar
                    continue

                # O restante da lógica de execução é a mesma do BotBase
                # stake = self.gestor.get_stake()
                # A lógica abaixo já foi movida para BotBase e está funcional.
                
                print(f"🔔 Sinal detectado: {tipo} | Padrão: {padrao}")

                # Stake e execução
                stake = self.gestor.get_stake()
                
                if self.modo_simulacao:
                    import random
                    resultado = random.choice(["win", "loss"])
                    self.gestor.registrar_resultado(resultado)
                    print(f"🧪 [SIMULAÇÃO] Resultado: {resultado}")
                else:
                    resposta = await self.executor.enviar_ordem(tipo, stake)
                    self.gestor.registrar_resultado(resposta["resultado"])
                    
                # Aqui você continua com a lógica do seu while loop.
                # A lógica de parar o bot em meta ou stop loss já está no BotBase
                # Vamos manter a sua lógica de exibir a taxa de acerto.
                
                self.estatistica.registrar_operacao(tipo, self.gestor.ultima_operacao, padrao)
                taxa = self.estatistica.calcular_taxa_acerto(padrao)
                print(f"📈 Taxa de acerto para '{padrao}': {taxa}%")

                await asyncio.sleep(10)
                
            except Exception as e:
                print(f"⚠️ Erro no loop principal: {e}. Tentando reconectar...")
                await self.reconectar_websocket()
                await asyncio.sleep(5)
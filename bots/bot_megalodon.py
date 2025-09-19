import asyncio
import json
import numpy as np
from datetime import datetime
from indicadores.indicadores import calcular_rsi, calcular_mm, calcular_bb, calcular_volatilidade
from core.modelo_neural import ModeloNeural
from core.bot_base import BotBase
from sklearn.metrics import accuracy_score

import os

class EstrategiaMegalodon:
    def __init__(self, config):
        self.config = config
        self.modelo = ModeloNeural()

        if os.path.exists("modelo_megalodon.h5") and os.path.exists("scaler_megalodon.pkl"):
            self.modelo.carregar_modelo("modelo_megalodon.h5")
            self.modelo.carregar_scaler("scaler_megalodon.pkl")
            print("✅ Modelo e scaler carregados com sucesso.")
        else:
            print("⚠️ Arquivos de IA não encontrados. Execute o script de treino primeiro.")



    def _preparar_dados(self, prices):
        if len(prices) < self.config["mm_periodo_longo"]:
            return None

        rsi = calcular_rsi(prices)
        mm_curta = calcular_mm(prices, self.config["mm_periodo_curto"])
        mm_longa = calcular_mm(prices, self.config["mm_periodo_longo"])
        vol = calcular_volatilidade(prices)

        features = np.array([rsi, mm_curta, mm_longa, vol]).reshape(1, -1)
        return features

    def decidir(self, prices, volatilidade=None, limiar_volatilidade=None):
        if volatilidade is not None and limiar_volatilidade is not None:
            if volatilidade < limiar_volatilidade:
                return None, "volatilidade_baixa"

        features = self._preparar_dados(prices)
        if features is None:
            return None, "dados_insuficientes"

        previsao = self.modelo.prever(features)

        if previsao == "up":
            return "CALL", "megalodon_detectou_alta"
        elif previsao == "down":
            return "PUT", "megalodon_detectou_baixa"

        return None, "neutro"

    async def treinar_com_historico_mercado(self, num_ticks, mercado):
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
        periodo_min = max(self.config.get("mm_periodo_longo", 20), 14)
        window_size = periodo_min

        for i in range(len(prices_data) - window_size - 1):
            subset = prices_data[i:i+window_size]
            next_price = prices_data[i+window_size]
            f = self._preparar_dados(subset)
            if f is not None:
                features.append(f[0])
                labels.append(1 if next_price > subset[-1] else 0)

        if features:
            X = np.array(features)
            y = np.array(labels)

            split = int(0.8 * len(X))
            X_train, X_test = X[:split], X[split:]
            y_train, y_test = y[:split], y[split:]

            self.modelo.treinar(X_train, y_train)
            preds = self.modelo.prever_lote(X_test)
            acc = accuracy_score(y_test, preds)
            print(f"✅ Treinamento concluído. Acurácia: {acc:.2%}")
        else:
            print("❌ Dados insuficientes para treinamento.")


# --- Bot Megalodon com integração à estratégia ---
class BotMegalodon(BotBase):
    def __init__(self, config, token, estatisticas_file):
        estrategia = EstrategiaMegalodon(config)
        super().__init__(config, token, estrategia, estatisticas_file)
        self.modo_simulacao = config.get("modo_simulacao", True)

    async def iniciar(self):
        await super().iniciar()

        if self.modo_simulacao:
            print("📚 Treinando rede neural com dados simulados...")
            await self.estrategia.treinar_com_historico_mercado(
                num_ticks=100,
                mercado=self.mercado
            )

import asyncio
import json
import numpy as np
from datetime import datetime
from indicadores.indicadores import calcular_rsi, calcular_mm, calcular_volatilidade
from core.modelo_neural import ModeloNeural
from core.bot_base import BotBase
from sklearn.metrics import accuracy_score
import os

# --- Estratégia Megalodon com IA (VERSÃO CORRIGIDA) ---
class EstrategiaMegalodon:
    def __init__(self, config):
        self.config = config
        self.modelo = ModeloNeural()
        self.ia_disponivel = False

        if os.path.exists("modelo_megalodon.h5") and os.path.exists("scaler_megalodon.pkl"):
            self.modelo.carregar_modelo("modelo_megalodon.h5")
            self.modelo.carregar_scaler("scaler_megalodon.pkl")
            self.ia_disponivel = True
            print("✅ Modelo e scaler carregados com sucesso.")
        else:
            print("⚠️ Arquivos de IA não encontrados. O bot usará apenas as regras de RSI/MM.")

    def _preparar_dados(self, prices):
        """Prepara os dados de entrada para o modelo de IA."""
        if len(prices) < self.config["mm_periodo_longo"]:
            return None

        rsi = calcular_rsi(prices)
        mm_curta = calcular_mm(prices, self.config["mm_periodo_curto"])
        mm_longa = calcular_mm(prices, self.config["mm_periodo_longo"])
        vol = calcular_volatilidade(prices)

        # Retorna o array de features
        return np.array([rsi, mm_curta, mm_longa, vol]).reshape(1, -1)

    def decidir(self, prices, volatilidade=None, limiar_volatilidade=None):
        """
        Decide a direção da operação, usando a IA se disponível,
        ou as regras clássicas como fallback.
        """
        # Checa se há dados suficientes para a decisão
        if len(prices) < self.config["mm_periodo_longo"]:
            return None, "dados_insuficientes"

        # 1. Prepara os features para a IA
        features = self._preparar_dados(prices)
        if features is None:
            return None, "dados_insuficientes"

        # 2. Usa a IA para prever a direção (o ponto chave!)
        if self.ia_disponivel:
            # A IA retorna a probabilidade para cada classe (0=Put, 1=Call)
            predicao = self.modelo.prever(features)

            # --- AJUSTE FEITO AQUI ---
            # O bloco try-except lida com o erro caso a IA retorne um valor inválido.
            try:
                # Tenta converter a predição para float para comparação
                probabilidade = float(predicao)

                if probabilidade > 0.5:
                    direcao = "CALL"
                else:
                    direcao = "PUT"
                    
            except (ValueError, TypeError) as e:
                # Se a conversão falhar, retorna None para ignorar a operação
                print(f"⚠️ ERRO: O modelo de IA retornou um valor inválido! Detalhes: {e}")
                print(f"Valor retornado: {predicao}")
                return None, "predicao_invalida"

            padrao = "IA"

            # Exemplo de uso do limiar de volatilidade com a IA
            if volatilidade < limiar_volatilidade:
                return None, "volatilidade_baixa"

            return direcao, padrao

        # 3. Se a IA não estiver disponível, usa as regras clássicas
        else:
            rsi = calcular_rsi(prices)
            mm_curta = calcular_mm(prices, self.config["mm_periodo_curto"])
            mm_longa = calcular_mm(prices, self.config["mm_periodo_longo"])

            # Regras de decisão "sniper" (RSI e MMs)
            if rsi > 70 and mm_curta > mm_longa and volatilidade > limiar_volatilidade:
                return "CALL", "sniper_alta"
            elif rsi < 30 and mm_curta < mm_longa and volatilidade > limiar_volatilidade:
                return "PUT", "sniper_baixa"
            else:
                return None, "condicoes_nao_alinhadas"

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


# --- Bot Megalodon com integração à estratégia (VERSÃO CORRIGIDA) ---
class BotMegalodon(BotBase):
    def __init__(self, config, token, estatisticas_file):
        estrategia = EstrategiaMegalodon(config)
        super().__init__(config, token, estrategia, estatisticas_file)
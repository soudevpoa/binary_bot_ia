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
        self.modelo = ModeloNeural(input_shape=200)
        
        self.ia_disponivel = False

        if os.path.exists("modelo_megalodon.h5") and os.path.exists("scaler_megalodon.pkl"):
            self.modelo.carregar("modelo_megalodon.h5") 
            self.modelo.carregar_scaler("scaler_megalodon.pkl")
            self.ia_disponivel = True
            print("✅ Modelo e scaler carregados com sucesso.")
        else:
            print("⚠️ Arquivos de IA não encontrados. O bot usará apenas as regras de RSI/MM.")


    def _preparar_dados(self, prices):
        """
        Prepara os dados de entrada para o modelo de IA, usando os últimos N preços.
        """
        # Pega o tamanho da janela do config.json (agora está como 200)
        window_size = self.config.get("tamanho_janela_ia", 200) 

        # 1. Checa se há dados suficientes
        if len(prices) < window_size:
            return None

        # 2. Pega os últimos 'window_size' preços
        features = prices[-window_size:] 

        # 3. Converte para array numpy e faz o reshape (1, 200)
        dados_formatados = np.array(features).reshape(1, -1)

        # 4. Normaliza (o scaler deve ser carregado/treinado no startup)
        if self.modelo and self.modelo.scaler:
            dados_normalizados = self.modelo.scaler.transform(dados_formatados)
            return dados_normalizados
        else:
            # Se o scaler não estiver carregado, use os dados brutos (e alerte, pois algo está errado)
            # O bot não deve operar se o scaler não estiver pronto.
            print("⚠️ ERRO: Scaler não carregado para normalização. Impossível usar a IA.")
            return None
    def decidir(self, prices, volatilidade=None, limiar_volatilidade=None):
        if len(prices) < self.config["mm_periodo_longo"]:
            return None, "dados_insuficientes"

        features = self._preparar_dados(prices)
        if features is None:
            return None, "dados_insuficientes"

        if self.ia_disponivel:
            predicao = self.modelo.prever(features)

            try:
                probabilidade = float(predicao)
                
                # ✅ AJUSTE PARA DEBUG: Veja o que a IA está prevendo.
                print(f"🤖 Probabilidade IA: {probabilidade:.4f}") 
                
                # ✅ AJUSTE PARA TESTE FINAL: Limite de confiança em 0.501
                # Isso força o bot a operar em quase todos os ticks, eliminando a zona de indecisão.
                LIMITE_CONFIANCA = 0.501 
                
                if probabilidade >= LIMITE_CONFIANCA:
                    direcao = "CALL"
                elif probabilidade <= (1 - LIMITE_CONFIANCA): # Que será 0.499
                    direcao = "PUT"
                else:
                    return None, "ia_indecisa"
                    
            except (ValueError, TypeError):
                return None, "predicao_invalida"

            padrao = "IA"

            if volatilidade < limiar_volatilidade:
                return None, "volatilidade_baixa"

            return direcao, padrao

        else:
            # 3. Se a IA não estiver disponível, usa as regras clássicas (seu fallback)
            rsi = calcular_rsi(prices)
            mm_curta = calcular_mm(prices, self.config["mm_periodo_curto"])
            mm_longa = calcular_mm(prices, self.config["mm_periodo_longo"])

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
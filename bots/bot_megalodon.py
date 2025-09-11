import asyncio
import numpy as np
from datetime import datetime
from indicadores.indicadores import calcular_rsi, calcular_mm, calcular_bb, calcular_volatilidade
from core.modelo_neural import ModeloNeural
from core.probabilidade_estatistica import ProbabilidadeEstatistica
from painel import streamlit_painel
from core.executor import Executor
from core.saldo import Saldo
from core.mercado import Mercado
from core.logger import Logger
from core.martingale_inteligente import MartingaleInteligente

class BotMegalodon:
    def __init__(self, config, token, estatisticas_file):
        self.config = config
        self.token = token
        self.modo_simulacao = config.get("modo_simulacao", True)
        self.prices = []
        self.modelo = ModeloNeural()
        self.estatistica = ProbabilidadeEstatistica(estatisticas_file)
        self.loss_count = 0
        self.profit_count = 0

    def treinar_com_historico(self):
        try:
            with open("historico_megalodon.json", "r") as f:
                linhas = f.readlines()
            features, labels = [], []
            for linha in linhas:
                dado = json.loads(linha)
                entrada = [dado["rsi"], dado["mm_curta"], dado["mm_longa"], dado["volatilidade"]]
                label = 1 if dado["resultado"] == "win" else 0
                features.append(entrada)
                labels.append(label)
            if features:
                X = np.array(features)
                y = np.array(labels)
                self.modelo.treinar(X, y)
                print(f"🔁 Modelo re-treinado com {len(features)} operações históricas.")
        except Exception as e:
            print(f"⚠️ Erro ao treinar com histórico: {e}")

    async def iniciar(self):
        mercado = Mercado("wss://ws.derivws.com/websockets/v3?app_id=1089", self.token, self.config["volatility_index"])
        await mercado.conectar()
        await mercado.autenticar(self.token)
        await mercado.subscrever_ticks(self.config["volatility_index"])
        asyncio.create_task(mercado.manter_conexao())
        if not self.modo_simulacao:
            self.treinar_com_historico()


        executor = Executor(mercado.ws, self.config["volatility_index"], self.config["stake"])
        saldo = Saldo(mercado.ws)
        logger = Logger()

        saldo_inicial = await saldo.consultar()
        painel = streamlit_painel(saldo_inicial)
        meta_lucro = saldo_inicial * self.config.get("meta_lucro_percentual", 0.10)
        stop_loss = saldo_inicial * self.config.get("stop_loss_percentual", 0.05)
        martingale = MartingaleInteligente(stake_base=self.config["stake"], max_niveis=3)

        print(f"🦈 Megalodon iniciado | Saldo: {saldo_inicial:.2f}")

        if self.modo_simulacao:
            print("📚 Treinando rede neural com dados simulados...")
            await self.treinar_modelo(mercado)

        while True:
            msg = await mercado.ws.recv()
            data = mercado.processar_tick(msg)
            if not data:
                continue

            price = data["price"]
            self.prices.append(price)
            if len(self.prices) > 60:
                self.prices.pop(0)

            tipo, padrao = None, "neutro"
            if len(self.prices) >= 30:
                rsi = calcular_rsi(self.prices)
                mm_curta = calcular_mm(self.prices, self.config["mm_periodo_curto"])
                mm_longa = calcular_mm(self.prices, self.config["mm_periodo_longo"])
                vol = calcular_volatilidade(self.prices)

                features = np.array([rsi, mm_curta, mm_longa, vol]).reshape(1, -1)
                previsao = self.modelo.prever(features)

                if previsao == "up":
                    tipo = "CALL"
                    padrao = "megalodon_detectou_alta"
                elif previsao == "down":
                    tipo = "PUT"
                    padrao = "megalodon_detectou_baixa"

            if tipo is None:
                print("⏳ Sem sinal. Aguardando próximo tick...")
                continue

            stake = martingale.get_stake()
            saldo_atual = await saldo.consultar()

            if self.modo_simulacao:
                import random
                resultado = random.choice(["win", "loss"])
                resposta = {
                    "resultado": resultado,
                    "payout": stake * 0.95,
                    "timestamp": "simulado",
                    "direcao": tipo,
                    "stake": stake,
                    "contract_id": "simulado"
                }
            else:
                resposta = await executor.enviar_ordem(tipo, stake)

            resultado = resposta["resultado"]
            payout = resposta["payout"]
            timestamp = resposta["timestamp"]
            direcao = resposta["direcao"]

            print(f"📊 Resultado: {resultado} | Direção: {direcao} | Stake: {stake:.2f}")

            painel.registrar_operacao(saldo_atual, resultado, stake, direcao)
            martingale.registrar_resultado(resultado)
            self.estatistica.registrar_operacao(direcao, resultado, padrao)
            taxa = self.estatistica.calcular_taxa_acerto(padrao)
            print(f"📈 Taxa de acerto '{padrao}': {taxa}%")

            self.loss_count += 1 if resultado == "loss" else 0
            self.profit_count += 1 if resultado == "win" else 0

            if (self.loss_count + self.profit_count) >= self.config.get("max_operacoes", 20):
                print("⏸️ Limite de operações atingido.")
                break
            if saldo_atual - saldo_inicial >= meta_lucro:
                print("🎯 Meta de lucro atingida.")
                break
            if saldo_atual - saldo_inicial <= -stop_loss:
                print("🛑 Stop loss atingido.")
                break

            await asyncio.sleep(10)

    async def treinar_modelo(self, mercado):
        prices_data = []
        for _ in range(100):
            msg = await mercado.ws.recv()
            data = mercado.processar_tick(msg)
            if data:
                prices_data.append(data["price"])

        features, labels = [], []
        for i in range(len(prices_data) - 1):
            subset = prices_data[:i+1]
            if len(subset) > self.config["mm_periodo_longo"]:
                rsi = calcular_rsi(subset)
                mm_curta = calcular_mm(subset, self.config["mm_periodo_curto"])
                mm_longa = calcular_mm(subset, self.config["mm_periodo_longo"])
                vol = calcular_volatilidade(subset)
                features.append([rsi, mm_curta, mm_longa, vol])
                labels.append(1 if prices_data[i+1] > prices_data[i] else 0)

        if features:
            X = np.array(features)
            y = np.array(labels)
            self.modelo.treinar(X, y)
            print("✅ Treinamento concluído.")

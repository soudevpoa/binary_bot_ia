import asyncio
import statistics
import json
import os
import numpy as np
from datetime import datetime, time

# Importações de classes e módulos
from core.mercado import Mercado
from core.executor import Executor
from core.logger import Logger
from core.saldo import Saldo
from core.desempenho import PainelDesempenho
from core.martingale_inteligente import MartingaleInteligente
from core.probabilidade_estatistica import ProbabilidadeEstatistica
from core.modelo_ia import ModeloIA
from indicadores.indicadores import calcular_rsi, calcular_mm, calcular_bb, calcular_volatilidade

# Funções auxiliares
def calcular_volatilidade(prices):
    if len(prices) < 2:
        return 0.0
    return statistics.stdev(prices)

def validar_resposta_contrato(resposta):
    if not isinstance(resposta, dict):
        return False, "resposta_invalida"

    status = resposta.get("resultado")
    payout = resposta.get("payout")
    contrato_id = resposta.get("contract_id", None)

    if status not in ["win", "loss"]:
        return False, "status_desconhecido"
    if not isinstance(payout, (int, float)) or payout <= 0:
        return False, "payout_invalido"
    if contrato_id is None:
        return False, "contrato_nao_executado"

    return True, "ok"

async def reconectar_websocket(mercado, saldo, executor, token, index, account_id=None):
    await mercado.conectar(account_id=account_id)
    await mercado.autenticar(token)
    await mercado.subscrever_ticks(index)
    executor.ws = mercado.ws
    saldo.ws = mercado.ws
    print("🔄 Reconexão concluída. Retomando operações...")

class BotIA:
    def __init__(self, config, token, estatisticas_file):
        self.historico_volatilidade = []
        self.config = config
        self.token = token
        self.modo_simulacao = config.get("modo_simulacao", False)
        self.prices = []
        self.loss_count = 0
        self.profit_count = 0
        self.modelo_ia = ModeloIA() # Instancia a classe do modelo de IA
        self.estatistica = ProbabilidadeEstatistica(estatisticas_file)

    async def iniciar(self, account_id=None):
        # 1. Carrega o APP_ID diretamente do arquivo .env de forma dinâmica
        app_id = os.getenv("APP_ID", "1089").strip()
        url_websocket = f"wss://ws.derivws.com/websockets/v3?app_id={app_id}"
        
        # Instancia a classe Mercado utilizando a URL montada com o .env
        mercado = Mercado(url_websocket, self.token, self.config["volatility_index"])
        
        # 2. Abre a conexão WebSocket inicial
        await mercado.conectar(account_id=account_id)
        
        # 3. Dispara IMEDIATAMENTE o loop único central em segundo plano para assumir o controle do recv()
        asyncio.create_task(mercado.manter_conexao(account_id=account_id))
        
        # 4. Pequeno delay de 1 segundo para garantir que o loop manter_conexao registrou o controle do WebSocket
        await asyncio.sleep(1)
        
        # 5. Envia as solicitações. O loop central gerencia e consome com segurança as respostas sem colidir corrotinas
        await mercado.autenticar(self.token)
        await mercado.subscrever_ticks(self.config["volatility_index"])

        # Ordem de parâmetros alinhada com o construtor real de core/executor.py
        executor = Executor(mercado.ws, self.config["volatility_index"], self.config["stake"], mercado)
        logger = Logger()
        saldo = Saldo(mercado.ws, mercado=mercado)

        saldo_inicial = await saldo.consultar()
        painel = PainelDesempenho(saldo_inicial)
        meta_lucro = saldo_inicial * self.config.get("meta_lucro_percentual", 0.10)
        stop_loss = saldo_inicial * self.config.get("stop_loss_percentual", 0.05)

        stake_base = max(round(saldo_inicial * 0.01, 2), 0.35)
        martingale = MartingaleInteligente(stake_base=stake_base)

        print(f"🧠 Bot de IA iniciado para {self.config['volatility_index']} | Saldo inicial: {saldo_inicial:.2f}")

        # Fase de treinamento do modelo
        if self.modo_simulacao:
            print("🚀 Treinando o modelo de IA em modo de simulação...")
            await self.treinar_modelo(mercado)

        while True:
            if self.config.get("usar_janela_horario", False):
                janelas_config = self.config.get("janelas_horario", [])
                agora = datetime.now().time()
                janelas = []
                for janela in janelas_config:
                    try:
                        inicio = datetime.strptime(janela["inicio"], "%H:%M").time()
                        fim = datetime.strptime(janela["fim"], "%H:%M").time()
                        janelas.append((inicio, fim))
                    except:
                        continue
                if not any(inicio <= agora <= fim for inicio, fim in janelas):
                    print("⏳ Fora da janela de operação. Aguardando...")
                    await asyncio.sleep(60)
                    continue

            try:
                msg_data = await mercado.queue.get()
                mercado.queue.task_done()
            except Exception as e:
                print(f"⚠️ Erro ao colher dados da fila: {e}")
                await asyncio.sleep(2)
                continue

            data = mercado.processar_tick(msg_data)
            if not data:
                continue

            price = data["price"]
            self.prices.append(price)

            if len(self.prices) > 60:
                self.prices.pop(0)

            tipo, padrao = None, "neutro"

            # Lógica de decisão baseada na IA
            if len(self.prices) >= 30:
                rsi_val = calcular_rsi(self.prices)
                mm_curta = calcular_mm(self.prices, self.config["mm_periodo_curto"])
                mm_longa = calcular_mm(self.prices, self.config["mm_periodo_longo"])
                volatilidade = calcular_volatilidade(self.prices)

                features = np.array([rsi_val, mm_curta, mm_longa, volatilidade]).reshape(1, -1)
                previsao = self.modelo_ia.prever(features)

                if previsao == "up":
                    tipo = "CALL"
                    padrao = "ia_previu_alta"
                elif previsao == "down":
                    tipo = "PUT"
                    padrao = "ia_previu_baixa"

            if tipo is None:
                continue

            if mercado.ws.state != "OPEN":
                print("🔌 WebSocket fechado. Tentando reconectar...")
                await reconectar_websocket(mercado, saldo, executor, self.token, self.config["volatility_index"], account_id=account_id)

            saldo_atual = await saldo.consultar()
            stake = martingale.get_stake()

            print(f"🔔 Sinal detectado: {tipo} | 💰 Stake: {stake:.2f}")

            if self.modo_simulacao:
                import random
                resultado = random.choice(["win", "loss"])
                print(f"🧪 Simulação ativa | Resultado: {resultado}")
                resposta = {
                    "resultado": resultado,
                    "payout": stake * 0.95,
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "direcao": tipo,
                    "stake": stake,
                    "contract_id": "simulado"
                }
            else:
                resposta = await executor.enviar_ordem(tipo, stake)

            valido, motivo = validar_resposta_contrato(resposta)
            if not valido:
                print(f"⚠️ Resposta inválida: {motivo}")
                print(f"📦 Resposta completa: {resposta}")
                continue

            resultado = resposta["resultado"]
            payout = resposta.get("payout", 0)
            # ✅ CORREÇÃO: Corrigido de 'response.get' para 'resposta.get' para evitar NameError/Coroutine issues
            timestamp = resposta.get("timestamp", datetime.now().strftime("%H:%M:%S"))
            direcao = resposta.get("direcao")

            print(f"📊 Resultado: {resultado}")
            if resultado in ["win", "loss"]:
                # 💡 NOTA: Se registrar_operacao ou registrar forem async def no seu core, adicione 'await' aqui!
                painel.registrar_operacao(saldo_atual, resultado, stake, direcao)
                martingale.registrar_resultado(resultado)
                
                self.estatistica.registrar_operacao(padrao, resultado)
                taxa = self.estatistica.calcular_taxa_acerto(padrao)
                
                print(f"📈 Taxa de acerto para '{padrao}': {taxa}%")
                logger.registrar(direcao, price, None, None, None, stake)

                print(f"📝 Operação registrada: {resultado.upper()} | Direção: {direcao} | Stake: {stake} | Payout: {payout} | Horário: {timestamp}")

                self.loss_count += 1 if resultado == "loss" else 0
                self.profit_count += 1 if resultado == "win" else 0

                operacoes = self.loss_count + self.profit_count
                if operacoes >= self.config.get("max_operacoes", 20):
                    print("⏸️ Limite de operações atingido.")
                    break

                lucro_total = saldo_atual - saldo_inicial
                if lucro_total >= meta_lucro:
                    print("🎯 Meta de lucro atingida.")
                    break
                if lucro_total <= -stop_loss:
                    print("🛑 Stop loss atingido.")
                    break

                await asyncio.sleep(10)
            else:
                print("⚠️ Erro ou resultado inválido. Continuando...")
    
    async def treinar_modelo(self, mercado):
        print("Coletando dados para o treinamento do modelo de IA...")
        prices_data = []
        for _ in range(100):
            msg_data = await mercado.queue.get()
            mercado.queue.task_done()
            data = mercado.processar_tick(msg_data)
            if data:
                prices_data.append(data["price"])
        
        features = []
        labels = []
        for i in range(len(prices_data) - 1):
            prices_subset = prices_data[:i+1]
            if len(prices_subset) > self.config["mm_periodo_longo"]:
                rsi_val = calcular_rsi(prices_subset)
                mm_curta = calcular_mm(prices_subset, self.config["mm_periodo_curto"])
                mm_longa = calcular_mm(prices_subset, self.config["mm_periodo_longo"])
                volatilidade = calcular_volatilidade(prices_subset)
                
                features.append([rsi_val, mm_curta, mm_longa, volatilidade])
                
                if prices_data[i+1] > prices_data[i]:
                    labels.append("up")
                else:
                    labels.append("down")
        
        if features:
            self.modelo_ia.treinar(np.array(features), np.array(labels))

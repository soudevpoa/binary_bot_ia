import asyncio
import statistics
import json
import os
from datetime import datetime, time

from core.mercado import Mercado
from core.executor import Executor
from core.logger import Logger
from core.soros import GerenciadorSoros
from core.saldo import Saldo
from core.desempenho import PainelDesempenho
from estrategias.martingale_inteligente import MartingaleInteligente
from core.probabilidade_estatistica import ProbabilidadeEstatistica

# Funções auxiliares
def calcular_volatilidade(prices):
    if len(prices) < 2:
        return 0.0
    return statistics.stdev(prices)

def calcular_limiar_dinamico(vols):
    if len(vols) < 5:
        return 0.02
    return sum(vols) / len(vols)

def atualizar_painel_json(price, volatilidade, limiar, tipo, padrao, lucro_total):
    dados = {
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "preco": price,
        "volatilidade": round(volatilidade, 5),
        "limiar": round(limiar, 5),
        "sinal": tipo or "Nenhum",
        "padrao": padrao,
        "lucro": round(lucro_total, 2)
    }
    caminho = os.path.join("dados", "painel_status.json")
    with open(caminho, "w") as f:
        json.dump(dados, f, indent=2)

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

async def reconectar_websocket(mercado, saldo, executor, token, index):
    await mercado.conectar()
    await mercado.autenticar(token)
    await mercado.subscrever_ticks(index)
    executor.ws = mercado.ws
    saldo.ws = mercado.ws
    print("🔄 Reconexão concluída. Retomando operações...")

class BotBase:
    def __init__(self, config, token, estrategia):
        self.historico_volatilidade = []
        self.config = config
        self.token = token
        self.estrategia = estrategia
        self.modo_simulacao = config.get("modo_simulacao", False)
        self.prices = []
        self.loss_count = 0
        self.profit_count = 0
        self.padroes_ignorados = {}

    def gerar_candles(self):
        candles = []
        for i in range(len(self.prices) - 1):
            candle = {
                "open": self.prices[i],
                "close": self.prices[i + 1],
                "high": max(self.prices[i], self.prices[i + 1]),
                "low": min(self.prices[i], self.prices[i + 1])
            }
            candles.append(candle)
        return candles

    async def iniciar(self):
        mercado = Mercado("wss://ws.derivws.com/websockets/v3?app_id=1089", self.token, self.config["volatility_index"])
        await mercado.conectar()
        if not await mercado.autenticar(self.token):
            return

        await mercado.subscrever_ticks(self.config["volatility_index"])
        asyncio.create_task(mercado.manter_conexao())

        executor = Executor(mercado.ws, self.config["volatility_index"], self.config["stake"])
        logger = Logger()
        saldo = Saldo(mercado.ws)

        saldo_inicial = await saldo.consultar()
        painel = PainelDesempenho(saldo_inicial)
        meta_lucro = saldo_inicial * self.config.get("meta_lucro_percentual", 0.10)
        stop_loss = saldo_inicial * self.config.get("stop_loss_percentual", 0.05)

        stake_base = max(round(saldo_inicial * 0.01, 2), 0.35)
        soros = GerenciadorSoros(stake_base, max_etapas=2)
        martingale = MartingaleInteligente(stake_base=stake_base, max_niveis=3)
        estatistica = ProbabilidadeEstatistica()

        print(f"📡 Bot iniciado para {self.config['volatility_index']} | Saldo inicial: {saldo_inicial:.2f}")

        while True:
            # ⏰ Verifica se está dentro da janela de operação
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
                msg = await mercado.ws.recv()
            except Exception as e:
                print(f"⚠️ Erro na conexão: {e}")
                await asyncio.sleep(2)
                await reconectar_websocket(mercado, saldo, executor, self.token, self.config["volatility_index"])
                continue

            data = mercado.processar_tick(msg)
            if not data:
                continue

            price = data["price"]
            print("🔄 Loop ativo | Preço atual:", price)
            self.prices.append(price)

            volatilidade = calcular_volatilidade(self.prices)
            self.historico_volatilidade.append(volatilidade)
            print(f"📊 Volatilidade atual: {volatilidade:.5f}")

            if len(self.historico_volatilidade) > 20:
                self.historico_volatilidade.pop(0)

            tipo, rsi, lower, upper, padrao = None, None, None, None, "neutro"

            if hasattr(self.estrategia, "tipo") and self.estrategia.tipo == "price_action":
                candles = self.gerar_candles()
                tipo, rsi, lower, upper, padrao = self.estrategia.decidir(candles)
                print(f"📊 Price Action detectado: {padrao}")
            else:
                limiar_dinamico = calcular_limiar_dinamico(self.historico_volatilidade)
                print(f"📐 Limiar dinâmico: {limiar_dinamico:.5f}")
                tipo, rsi, lower, upper, padrao = self.estrategia.decidir(self.prices, volatilidade, limiar_dinamico)

            if padrao == "volatilidade_baixa":
                self.padroes_ignorados[padrao] = self.padroes_ignorados.get(padrao, 0) + 1

            if tipo is None:
                print("⏳ Nenhum sinal gerado. Aguardando próximo tick.")
                continue

            # 🧠 Verifica taxa mínima de acerto
            taxa_acerto = estatistica.calcular_taxa_acerto(padrao)
            limite_taxa = self.config.get("taxa_minima_acerto", 60)
            if taxa_acerto < limite_taxa:
                print(f"🚫 Taxa de acerto para '{padrao}' é baixa ({taxa_acerto}%). Ignorando sinal.")
                continue

            if mercado.ws.state != "OPEN":
               print("🔌 WebSocket fechado. Tentando reconectar...")
               await reconectar_websocket(mercado, saldo, executor, self.token, self.config["volatility_index"])

               saldo_atual = await saldo.consultar()
               stake_soros = soros.get_stake(saldo_atual)
               stake = martingale.get_stake()

               print(f"🔔 Sinal detectado: {tipo} | 💰 Stake: {stake:.2f}")

            if self.modo_simulacao:
               import random
               resultado = random.choice(["win", "loss"])
               print(f"🧪 Simulação ativa | Resultado: {resultado}")
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

                valido, motivo = validar_resposta_contrato(resposta)
                if not valido:
                    print(f"⚠️ Resposta inválida: {motivo}")
                    print(f"📦 Resposta completa: {resposta}")
                    continue

                resultado = resposta["resultado"]
                payout = resposta.get("payout", 0)
                timestamp = resposta.get("timestamp")
                direcao = resposta.get("direcao")

                print(f"📊 Resultado: {resultado}")
                if resultado in ["win", "loss"]:
                    painel.registrar_operacao(saldo_atual, resultado, stake, direcao)
                    soros.registrar_resultado(resultado)
                    martingale.registrar_resultado(resultado)
                    estatistica.registrar_operacao(direcao, resultado, padrao)
                    taxa = estatistica.calcular_taxa_acerto(padrao)
                    print(f"📈 Taxa de acerto para '{padrao}': {taxa}%")
                    logger.registrar(direcao, price, rsi, lower, upper, stake)

                    print(f"📝 Operação registrada: {resultado.upper()} | Direção: {direcao} | Stake: {stake} | Payout: {payout} | Horário: {timestamp}")

                    self.loss_count += 1 if resultado == "loss" else 0
                    self.profit_count += 1 if resultado == "win" else 0

                    operacoes = self.loss_count + self.profit_count
                    if operacoes >= self.config.get("max_operacoes", 20):
                        print("⏸️ Limite de operações atingido.")
                        break

                    lucro_total = saldo_atual - saldo_inicial
                    atualizar_painel_json(price, volatilidade, limiar_dinamico, tipo, padrao, lucro_total)

                    if lucro_total >= meta_lucro:
                        print("🎯 Meta de lucro atingida.")
                        break
                    if lucro_total <= -stop_loss:
                        print("🛑 Stop loss atingido.")
                        break

                    await asyncio.sleep(10)
                else:
                    print("⚠️ Erro ou resultado inválido. Continuando...")
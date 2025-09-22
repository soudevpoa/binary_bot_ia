import asyncio
import json
import statistics
import random
from datetime import datetime, time
from core.gestores.stake_fixa import StakeFixa
from core.gestores.soros import Soros
from core.logger import Logger
from core.mercado import Mercado
from core.executor import Executor
from core.saldo import Saldo
from core.desempenho import PainelDesempenho
from core.probabilidade_estatistica import ProbabilidadeEstatistica
from indicadores.indicadores import calcular_volatilidade
from core.gestores.martingale_inteligente import MartingaleInteligente
from core.gestores.martingale_tradicional import MartingaleTradicional

# Funções auxiliares
def validar_resposta_contrato(resposta):
    if not isinstance(resposta, dict):
        return False, "resposta_invalida"
    status = resposta.get("resultado")
    payout = resposta.get("payout")
    contrato_id = resposta.get("contract_id", None)
    status_validos = ["win", "loss"]
    status_ignorados = ["sold", "expired", "cancelled"]
    if status in status_ignorados:
        print(f"ℹ️ Contrato encerrado com status '{status}' — operação ignorada.")
        return False, "status_ignorado"
    if not isinstance(payout, (int, float)) or payout <= 0:
        return False, "payout_invalido"
    if contrato_id is None:
        return False, "contrato_nao_executado"
    if status.lower() in status_validos:
        return True, status.lower()
    elif status.lower() == "open":
        print("⚠️ Contrato ainda aberto — aguardando encerramento.")
        return False, "contrato_aberto"
    else:
        print(f"⚠️ Status desconhecido recebido: '{status}'")
        return False, "status_desconhecido"

async def reconectar_websocket(mercado, saldo, executor, token, index):
    await mercado.conectar()
    await mercado.autenticar(token)
    await mercado.subscrever_ticks(index)
    executor.ws = mercado.ws
    saldo.ws = mercado.ws
    print("🔄 Reconexão concluída. Retomando operações...")

# --- CLASSE BOTBASE ---
class BotBase:
    def __init__(self, config, token, estrategia, estatisticas_file):
        self.config = config
        self.token = token
        self.estrategia = estrategia
        self.prices = []
        self.sequencia_resultados = []
        self.loss_virtual_ativa = config.get("usar_loss_virtual", False)
        self.limite_loss_virtual = int(config.get("limite_loss_virtual", 4))
        self.contador_loss_virtual = 0
        self.mercado = None
        self.executor = None
        self.logger = Logger()
        self.saldo = None
        self.painel = None
        self.estatistica = ProbabilidadeEstatistica(estatisticas_file)
        self.gestor = self._criar_gestor()

    def _criar_gestor(self):
        tipo_gestor = self.config.get("gestor", "stake_fixa")
        stake_base = float(self.config.get("stake_base", 1))
        
        if tipo_gestor == "soros":
            return Soros(
                stake_base=stake_base,
                max_etapas=int(self.config.get("soros_max_etapas", 2)),
                stake_max=self.config.get("soros_stake_max"),
                reinvestir=self.config.get("soros_reinvestir", "lucro")
            )
        elif tipo_gestor == "martingale":
            tipo_martingale = self.config.get("tipo_martingale", "tradicional")
            if tipo_martingale == "inteligente":
                return MartingaleInteligente(
                    stake_base=stake_base,
                    fator=float(self.config.get("martingale_fator", 2)),
                    limite=int(self.config.get("martingale_limite", 3))
                )
            else:
                return MartingaleTradicional(
                    stake_base=stake_base,
                    fator=float(self.config.get("martingale_fator", 2)),
                    limite=int(self.config.get("martingale_limite", 3))
                )
        else:
            return StakeFixa(valor=stake_base)

    async def _executar_operacao(self, tipo, stake, padrao):
        if self.config.get("modo_simulacao", False):
            resultado = random.choice(["win", "loss"])
            payout = stake * random.uniform(1.7, 1.95) if resultado == "win" else 0.0
            if self.loss_virtual_ativa:
                if resultado == "loss":
                    self.contador_loss_virtual += 1
                else:
                    self.contador_loss_virtual = 0
                print(f"🧪 Contador de Loss Virtual: {self.contador_loss_virtual}/{self.limite_loss_virtual}")
            return {
                "resultado": resultado,
                "payout": payout,
                "stake": stake,
                "simulacao": True,
                "direcao": tipo,
                "padrao": padrao
            }
        else:
            if self.loss_virtual_ativa:
                resultado_simulado = random.choice(["win", "loss"])
                if resultado_simulado == "loss":
                    self.contador_loss_virtual += 1
                else:
                    self.contador_loss_virtual = 0
                print(f"🧪 Contador de Loss Virtual: {self.contador_loss_virtual}/{self.limite_loss_virtual}")
                if self.contador_loss_virtual < self.limite_loss_virtual:
                    print("👻 Ainda em Loss Virtual — operação real será ignorada.")
                    return None
            print("✅ Escudo de Loss Virtual desativado — operação real será executada.")
            resposta = await self.executor.enviar_ordem(tipo, stake)
            valido, motivo = validar_resposta_contrato(resposta)
            if not valido:
                raise Exception(f"Resposta inválida da API: {motivo}")
            resposta["simulacao"] = False
            return resposta

    async def iniciar(self):
        try:
            self.mercado = Mercado(
                "wss://ws.derivws.com/websockets/v3?app_id=1089",
                self.token,
                self.config["volatility_index"]
            )
            await self.mercado.conectar()
            if not await self.mercado.autenticar(self.token):
                return
            await self.mercado.subscrever_ticks(self.config["volatility_index"])
            asyncio.create_task(self.mercado.manter_conexao())

            # 🚨 CORREÇÃO PRINCIPAL: Conversão do stake_base para float aqui
            self.executor = Executor(
                self.mercado.ws,
                self.config["volatility_index"],
                float(self.config["stake_base"])
            )
            self.saldo = Saldo(self.mercado.ws)
            saldo_inicial = await self.saldo.consultar()
            self.painel = PainelDesempenho(saldo_inicial)
            print(f"🤖 Bot iniciado para {self.config['volatility_index']} | Saldo inicial: {saldo_inicial:.2f}")
            if self.config.get("modo_simulacao", False):
                print("🚀 BOT INICIADO EM MODO SIMULAÇÃO — Nenhuma ordem real será enviada!")
            else:
                print("⚡ BOT INICIADO EM MODO REAL — Ordens reais serão enviadas!")

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
                    msg = await self.mercado.ws.recv()
                    data = self.mercado.processar_tick(msg)
                    if not data:
                        continue
                except Exception as e:
                    print(f"⚠️ Erro na conexão: {e}")
                    await asyncio.sleep(2)
                    await reconectar_websocket(self.mercado, self.saldo, self.executor, self.token, self.config["volatility_index"])
                    continue
                
                price = data["price"]
                self.prices.append(price)
                if len(self.prices) > 60:
                    self.prices.pop(0)

                volatilidade = calcular_volatilidade(self.prices)
                limiar_volatilidade = float(self.config.get("limiar_volatilidade", 0.0005))
                decisao = self.estrategia.decidir(self.prices, volatilidade, limiar_volatilidade)
                if not isinstance(decisao, (list, tuple)):
                    print("⚠️ Estratégia retornou um valor inesperado:", decisao)
                    continue
                tipo = decisao[0] if len(decisao) > 0 else None
                padrao = decisao[-1] if len(decisao) > 0 else None
                if tipo is None:
                    continue

                try:
                    saldo_atual = await self.saldo.consultar()
                except Exception as e:
                    print(f"🔌 Falha ao consultar saldo ({e}). Tentando reconectar...")
                    await reconectar_websocket(self.mercado, self.saldo, self.executor, self.token, self.config["volatility_index"])
                    continue
                
                stake = self.gestor.get_stake()
                print(f"🔔 Sinal detectado: {tipo} | 💰 Stake: {stake:.2f}")

                try:
                    resposta = await self._executar_operacao(tipo, stake, padrao)
                    if resposta is None:
                        continue
                    resultado = resposta["resultado"]
                    direcao = resposta.get("direcao", tipo)
                    stake_executada = resposta.get("stake", stake)
                    self.gestor.registrar_resultado(
                        resultado,
                        payout=resposta.get("payout", 0.0),
                        stake_executada=stake_executada
                    )
                    if padrao:
                        self.estatistica.registrar_operacao(padrao, resultado)
                    etapa = getattr(self.gestor, "contador", getattr(self.gestor, "etapa", 1))
                    print(f"📊 Gestor: {self.config.get('gestor')} | Etapa: {etapa}")
                    self.sequencia_resultados.append(resultado)
                    if len(self.sequencia_resultados) > 5:
                        self.sequencia_resultados.pop(0)
                    print(f"📉 Últimos resultados: {' → '.join(self.sequencia_resultados)}")
                    if padrao:
                        taxa = self.estatistica.calcular_taxa_acerto(padrao)
                        print(f"📈 Taxa de acerto para '{padrao}': {taxa}%")
                    self.logger.registrar(direcao, price, None, None, None, stake)
                    print(
                        f"📝 Operação registrada: {resultado.upper()} | Direção: {direcao} | "
                        f"Stake: {stake} | Payout: {resposta.get('payout', 0)} | Horário: {datetime.now().strftime('%H:%M:%S')}"
                    )
                    if padrao and self.estatistica.estatisticas.get(padrao, {}).get("total", 0) >= self.config.get("max_operacoes", 20):
                        print("⏸️ Limite de operações atingido.")
                        break
                except Exception as e:
                    print(f"🔌 Falha na execução da ordem ({e}).")
                    continue
        except Exception as e:
            raise e
        finally:
            print("👋 Fechando bot. Salvando estatísticas...")
            if hasattr(self, 'estatistica'):
                self.estatistica.salvar_estatisticas()
            print("Bot encerrado.")
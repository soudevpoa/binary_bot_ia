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
from core.martingale_inteligente import MartingaleInteligente
from core.probabilidade_estatistica import ProbabilidadeEstatistica
from indicadores.indicadores import calcular_volatilidade
from core.gestores.soros import Soros
from core.gestores.stake_fixa import StakeFixa
from core.gestores.martingale_inteligente import MartingaleInteligente
from core.gestores.martingale_tradicional import MartingaleTradicional


# Funções auxiliares
def validar_resposta_contrato(resposta):
    """
    Valida a resposta do contrato retornada pela API.
    Retorna (True, "ok") se for win/loss.
    Retorna (False, motivo) para status ignorados ou desconhecidos.
    """
    if not isinstance(resposta, dict):
        return False, "resposta_invalida"

    status = resposta.get("resultado")
    payout = resposta.get("payout")
    contrato_id = resposta.get("contract_id", None)

    # Status válidos para operação
    status_validos = ["win", "loss"]

    # Status que não são erro, mas não contam como operação
    status_ignorados = ["sold", "expired", "cancelled"]

    # Ignora status neutros
    if status in status_ignorados:
        print(f"ℹ️ Contrato encerrado com status '{status}' — operação ignorada.")
        return False, "status_ignorado"

    # Aceita apenas win/loss como válidos
    if status not in status_validos:
        print(f"⚠️ Status desconhecido recebido: '{status}'")
        return False, "status_desconhecido"

    # Valida payout
    if not isinstance(payout, (int, float)) or payout <= 0:
        return False, "payout_invalido"

    # Valida contrato_id
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


# --- CLASSE BOTBASE ---
class BotBase:
    def __init__(self, config, token, estrategia, estatisticas_file):
        self.config = config
        self.token = token
        self.estrategia = estrategia
        self.prices = []
        self.sequencia_resultados = []
        self.loss_virtual_ativa = config.get("usar_loss_virtual", False)
        self.limite_loss_virtual = config.get("limite_loss_virtual", 4)
        self.contador_loss_virtual = 0
        self.loss_count = 0
        self.profit_count = 0
        self.mercado = None
        self.executor = None
        self.logger = Logger()
        self.saldo = None
        self.painel = None
        self.loss_virtual_count = 0
        self.estatistica = ProbabilidadeEstatistica(estatisticas_file)
        self.gestor = self._criar_gestor()

    def _criar_gestor(self):
        tipo_gestor = self.config.get("gestor", "stake_fixa")

        if tipo_gestor == "soros":
            from core.gestores.soros import Soros
            return Soros(
                stake_base=self.config.get("stake_base", 1),
                max_etapas=self.config.get("soros_max_etapas", 2),
                stake_max=self.config.get("soros_stake_max"),
                reinvestir=self.config.get("soros_reinvestir", "lucro")
            )

        elif tipo_gestor == "martingale":
            tipo_martingale = self.config.get("tipo_martingale", "tradicional")

            if tipo_martingale == "inteligente":
                from core.gestores.martingale_inteligente import MartingaleInteligente
                return MartingaleInteligente(
                    stake_base=self.config.get("stake_base", 1),
                    fator=self.config.get("martingale_fator", 2),
                    limite=self.config.get("martingale_limite", 3)
                )
            else:
                from core.gestores.martingale_tradicional import MartingaleTradicional
                return MartingaleTradicional(
                    stake_base=self.config.get("stake_base", 1),
                    fator=self.config.get("martingale_fator", 2),
                    limite=self.config.get("martingale_limite", 3)
                )

        else:
            from core.gestores.stake_fixa import StakeFixa
            return StakeFixa(valor=self.config.get("stake_base", 1))


    def registrar_resultado_virtual(self, resultado):
        # 🧠 Atualiza contador de perdas simuladas
        if resultado == "loss":
            self.loss_virtual_count += 1
        else:
            self.loss_virtual_count = 0  # Reinicia se for win (ou mantém, se quiser lógica diferente)

        # 📊 Log do estado atual
        print(f"🧪 Contador de Loss Virtual: {self.loss_virtual_count}/{self.config.get('limite_loss_virtual', 4)}")

        # 🎯 Verifica se atingiu o limite
        if self.loss_virtual_count >= self.config.get("limite_loss_virtual", 4):
            print("✅ Limite de Loss Virtual atingido — próxima operação será real.")
            self.loss_virtual_count = 0  # Reseta o contador
            return True  # Sinaliza que pode operar de verdade

        # 👻 Ainda em modo de simulação
        print("👻 Operação simulada — escudo de Loss Virtual ainda ativo.")
        return False




    # --- INÍCIO DA FUNÇÃO INICIAR COM AS CORREÇÕES E AJUSTES ---
    async def iniciar(self):
        # AQUI FOI INSERIDO O BLOCO TRY...FINALLY PRINCIPAL.
        # Ele garante que as estatísticas sejam salvas ao final da execução.
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

            self.executor = Executor(
                self.mercado.ws,
                self.config["volatility_index"],
                self.config["stake_base"]
            )
            self.saldo = Saldo(self.mercado.ws)
            saldo_inicial = await self.saldo.consultar()
            self.painel = PainelDesempenho(saldo_inicial)

            meta_lucro = saldo_inicial * self.config.get("meta_lucro_percentual", 0.10)
            stop_loss = saldo_inicial * self.config.get("stop_loss_percentual", 0.05)
            
            print(f"🤖 Bot iniciado para {self.config['volatility_index']} | Saldo inicial: {saldo_inicial:.2f}")

            # Aviso inicial
            if self.config.get("modo_simulacao", False):
                print("🚀 BOT INICIADO EM MODO SIMULAÇÃO — Nenhuma ordem real será enviada!")
            else:
                print("⚡ BOT INICIADO EM MODO REAL — Ordens reais serão enviadas!")

            while True:
                # 1️⃣ Checa janela de operação
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

                # 2️⃣ Recebe tick
                try:
                    msg = await self.mercado.ws.recv()
                except Exception as e:
                    print(f"⚠️ Erro na conexão: {e}")
                    await asyncio.sleep(2)
                    await reconectar_websocket(
                        self.mercado, self.saldo, self.executor,
                        self.token, self.config["volatility_index"]
                    )
                    continue

                # 3️⃣ Processa tick
                data = self.mercado.processar_tick(msg)
                if not data:
                    continue

                price = data["price"]
                self.prices.append(price)
                if len(self.prices) > 60:
                    self.prices.pop(0)

                # 4️⃣ Decide operação
                volatilidade = calcular_volatilidade(self.prices)
                limiar_volatilidade = self.config.get("limiar_volatilidade", 0.0005)
                
                decisao = self.estrategia.decidir(self.prices, volatilidade, limiar_volatilidade)
                
                if not isinstance(decisao, (list, tuple)):
                    print("⚠️ Estratégia retornou um valor inesperado:", decisao)
                    continue

                tipo = decisao[0] if len(decisao) > 0 else None
                padrao = decisao[-1] if len(decisao) > 0 else None
                
                if tipo is None:
                    continue

                # 5️⃣ Checa conexão
                ws = self.mercado.ws
                if ws is None or (hasattr(ws, "open") and not ws.open):
                    print("🔌 WebSocket fechado. Tentando reconectar...")
                    await reconectar_websocket(self.mercado, self.saldo, self.executor, self.token, self.config["volatility_index"])
                    continue
                if not hasattr(ws, "open"):
                    try:
                        await ws.ping()
                    except Exception:
                        print("🔌 WebSocket sem resposta. Tentando reconectar...")
                        await reconectar_websocket(self.mercado, self.saldo, self.executor, self.token, self.config["volatility_index"])
                        continue

                # 6️⃣ Consulta saldo
                try:
                    saldo_atual = await self.saldo.consultar()
                except Exception as e:
                    print(f"🔌 Falha ao consultar saldo ({e}). Tentando reconectar...")
                    await reconectar_websocket(
                        self.mercado, self.saldo, self.executor,
                        self.token, self.config["volatility_index"]
                    )
                    continue

                # 7️⃣ Calcula stake e executa
                stake = self.gestor.get_stake()
                print(f"🔔 Sinal detectado: {tipo} | 💰 Stake: {stake:.2f}")

                try:
                    if self.config.get("modo_simulacao", False):
                        if self.config.get("usar_loss_virtual", False):
                            resultado_simulado = random.choice(["win", "loss"])
                            entrou_na_real = self.registrar_resultado_virtual(resultado_simulado)

                            if entrou_na_real:
                                print("🎯 Limite de Loss virtual atingido. Executando operação real simulada.")
                                resultado = random.choice(["win", "loss"])
                                payout = stake * random.uniform(1.7, 1.95) if resultado == "win" else 0.0
                            else:
                                print(f"👻 Loss virtual registrado. Total: {self.loss_virtual_count}")
                                resultado = resultado_simulado
                                payout = stake * random.uniform(1.7, 1.95) if resultado == "win" else 0.0

                            resposta = {
                                "resultado": resultado,
                                "payout": payout,
                                "stake": stake,
                                "simulacao": True,
                                "direcao": tipo,
                                "padrao": padrao
                            }

                        else:
                            resultado = random.choice(["win", "loss"])
                            payout = stake * random.uniform(1.7, 1.95) if resultado == "win" else 0.0
                            resposta = {
                                "resultado": resultado,
                                "payout": payout,
                                "stake": stake,
                                "simulacao": True,
                                "direcao": tipo,
                                "padrao": padrao
                            }

                    else:
                        #  Verifica se deve simular antes de operar
                        if self.config.get("usar_loss_virtual", False):
                            resultado_simulado = random.choice(["loss", "win"])
                            entrou_na_real = self.registrar_resultado_virtual(resultado_simulado)

                            print(f"🧪 Contador de Loss Virtual: {self.loss_virtual_count}/{self.config.get('limite_loss_virtual', 4)}")

                            if not entrou_na_real:
                                print("👻 Ainda em Loss Virtual — operação simulada, sem entrada real.")
                                continue  # ⛔️ Pula a operação real até atingir o limite
                            else:
                                print("✅ Escudo de Loss Virtual desativado — operação real será executada.")

                        #  Executa operação real
                        resposta = await self.executor.enviar_ordem(tipo, stake)
                        valido, motivo = validar_resposta_contrato(resposta)
                        if not valido:
                            print(f"⚠️ Resposta inválida: {motivo}")
                            continue
                        resposta["simulacao"] = False



                    # ATENÇÃO: UNIFICAMOS O CÓDIGO DE ESTATÍSTICAS AQUI
                    resultado = resposta["resultado"]
                    direcao = resposta.get("direcao", tipo)
                    stake_executada = resposta.get("stake", stake)
                    
                    # A PARTIR DE AGORA, SEMPRE USAMOS self.estatistica
                    if resultado in ("win", "loss"):
                        self.gestor.registrar_resultado(
                            resultado,
                            payout=resposta.get("payout", 0.0),
                            stake_executada=stake_executada
                        )
                        self.estatistica.registrar_operacao(direcao, resultado, padrao)
                    # 📊 Log de stake atual
                    etapa = getattr(self.gestor, "contador", getattr(self.gestor, "etapa", 1))
                    print(f"📊 Stake atual: {stake:.2f} | Gestor: {self.config.get('gestor')} | Etapa: {etapa}")

                    # 📉 Log de sequência de resultados
                    self.sequencia_resultados.append(resultado)
                    if len(self.sequencia_resultados) > 5:
                        self.sequencia_resultados.pop(0)
                    print(f"📉 Últimos resultados: {' → '.join(self.sequencia_resultados)}")
    

                    taxa = self.estatistica.calcular_taxa_acerto(padrao)
                    print(f"📈 Taxa de acerto para '{padrao}': {taxa}%")

                    self.logger.registrar(direcao, price, None, None, None, stake)
                    print(
                        f"📝 Operação registrada: {resultado.upper()} | Direção: {direcao} | "
                        f"Stake: {stake} | Payout: {resposta.get('payout', 0)} | Horário: {datetime.now().strftime('%H:%M:%S')}"
                    )
                    
                    # Fim do loop?
                    if self.estatistica.estatisticas.get(padrao, {}).get("total", 0) >= self.config.get("max_operacoes", 20):
                        print("⏸️ Limite de operações atingido.")
                        break

                except Exception as e:
                    print(f"🔌 Falha ao enviar ordem ({e}). Tentando reconectar...")
                    await reconectar_websocket(
                        self.mercado,
                        self.saldo,
                        self.executor,
                        self.token,
                        self.config["volatility_index"]
                    )
                    continue

        except Exception as e:
            # ESTE BLOCO CAPTURA ERROS GERAIS, como KeyboardInterrupt (Ctrl+C).
            print(f"⚠️ O bot foi interrompido por um erro fatal: {e}")
            
        finally:
            # AQUI É O PONTO CRÍTICO: SALVAMOS AS ESTATÍSTICAS.
            # Esta linha será executada sempre que o bot for encerrado.
            print("👋 Fechando bot. Salvando estatísticas...")
            self.estatistica.salvar_estatisticas()
            print("Bot encerrado.")
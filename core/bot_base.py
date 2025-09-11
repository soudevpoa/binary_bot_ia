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
        self.loss_count = 0
        self.profit_count = 0
        self.mercado = None
        self.executor = None
        self.logger = Logger()
        self.saldo = None
        self.painel = None
        self.estatistica = ProbabilidadeEstatistica(estatisticas_file)
        self.gestor = self._criar_gestor()

    def _criar_gestor(self):
        modo = self.config.get("modo_operacao", "martingale")
        stake_base = float(self.config.get("stake_base", 1.0))
        stake_max = self.config.get("stake_max")

        if modo == "fixo":
            fixo_cfg = self.config.get("fixo", {})
            return StakeFixa(fixo_cfg.get("valor", stake_base))

        if modo == "soros":
            soros_cfg = self.config.get("soros", {})
            return Soros(
                stake_base=stake_base,
                max_niveis=soros_cfg.get("max_niveis", 2),
                reinvestir=soros_cfg.get("reinvestir", "lucro"),
                stake_max=stake_max
            )

        if modo == "dinamico":
            # Guarda configurações para decidir no momento de operar
            self._dinamico_cfg = self.config.get("dinamico", {})
            # default inicial
            return StakeFixa(self._dinamico_cfg.get("fixo_valor", stake_base))

        # default: martingale
        return MartingaleInteligente(
            stake_base=stake_base,
            max_niveis=self.config.get("max_niveis", 3),
            fator_multiplicador=self.config.get("fator_multiplicador", 2.0),
            stake_max=stake_max
        )

    async def iniciar(self):
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

        # Estatísticas de simulação
        total_ops = 0
        wins = 0
        losses = 0
        saldo = 0.0
        historico = []

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
            # Chama a estratégia e captura tudo
            decisao = self.estrategia.decidir(
                self.prices, volatilidade, limiar_volatilidade     
                
            )

            # Garante que é uma tupla/lista
            if not isinstance(decisao, (list, tuple)):
                print("⚠️ Estratégia retornou um valor inesperado:", decisao)
                continue

            # Extrai tipo e padrao de forma segura
            tipo = decisao[0] if len(decisao) > 0 else None
            padrao = decisao[-1] if len(decisao) > 0 else None  # último elemento como padrão

            # Se não houver tipo, pula
            if tipo is None:
                continue


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
                    resultado = random.choice(["win", "loss"])
                    payout = stake * random.uniform(1.7, 1.95) if resultado == "win" else 0.0
                    resposta = {
                        "resultado": resultado,
                        "payout": payout,
                        "stake": stake,
                        "simulacao": True
                    }
                else:
                    resposta = await self.executor.enviar_ordem(tipo, stake)
                    valido, motivo = validar_resposta_contrato(resposta)
                    if not valido:
                        print(f"⚠️ Resposta inválida: {motivo}")
                        continue
                    resposta["simulacao"] = False

                # Atualiza gestor
                resultado = resposta["resultado"]
                payout = resposta.get("payout", 0.0)
                stake_executada = resposta.get("stake", stake)

                if resultado in ("win", "loss"):
                    self.gestor.registrar_resultado(
                        resultado,
                        payout=payout,
                        stake_executada=stake_executada
                    )

                # Estatísticas no modo simulação
                if self.config.get("modo_simulacao", False):
                    total_ops += 1
                    if resultado == "win":
                        wins += 1
                        saldo += payout
                    else:
                        losses += 1
                        saldo -= stake_executada

                    historico.append({
                        "op": total_ops,
                        "resultado": resultado,
                        "stake": stake_executada,
                        "payout": payout,
                        "saldo": round(saldo, 2)
                    })

                    print(f"🧪 [SIMULAÇÃO] Op {total_ops} | Resultado: {resultado} | "
                          f"Stake: {stake_executada} | Payout: {payout} | Saldo: {round(saldo, 2)}")

                    # Relatório final
                    if total_ops >= 20:
                        taxa_acerto = (wins / total_ops) * 100 if total_ops > 0 else 0
                        print("\n📊 RELATÓRIO FINAL DE SIMULAÇÃO")
                        print(f"Total de operações: {total_ops}")
                        print(f"Wins: {wins} | Losses: {losses}")
                        print(f"Taxa de acerto: {taxa_acerto:.2f}%")
                        print(f"Lucro/Prejuízo final: {round(saldo, 2)}\n")

                        print("📜 Histórico de operações:")
                        for op in historico:
                            print(f"Op {op['op']:02d} | {op['resultado'].upper()} | "
                                  f"Stake: {op['stake']} | Payout: {op['payout']} | Saldo: {op['saldo']}")

                        # Salva em JSON
                        with open("relatorio_simulacao.json", "w", encoding="utf-8") as f:
                            json.dump(historico, f, ensure_ascii=False, indent=4)
                        print("💾 Relatório salvo em relatorio_simulacao.json")
                        break

                # 8️⃣ Valida e processa resposta (Modo real)
                else:
                    resultado = resposta["resultado"]
                    payout = resposta.get("payout", 0)
                    timestamp = resposta.get("timestamp")
                    direcao = resposta.get("direcao")

                    print(f"📊 Resultado: {resultado}")
                    if resultado in ["win", "loss"]:
                        self.painel.registrar_operacao(saldo_atual, resultado, stake, direcao)
                        self.estatistica.registrar_operacao(direcao, resultado, padrao)

                        taxa = self.estatistica.calcular_taxa_acerto(padrao)
                        print(f"📈 Taxa de acerto para '{padrao}': {taxa}%")

                        self.logger.registrar(direcao, price, None, None, None, stake)
                        print(
                            f"📝 Operação registrada: {resultado.upper()} | Direção: {direcao} | "
                            f"Stake: {stake} | Payout: {payout} | Horário: {timestamp}"
                        )

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
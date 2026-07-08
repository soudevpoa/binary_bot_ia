import asyncio
import json
import statistics
import random
import time
import os
from datetime import datetime
from core.gestores.stake_fixa import StakeFixa
from core.gestores.soros import Soros
from core.logger import Logger
from core.mercado import Mercado
from core.executor import Executor
from core.saldo import Saldo
from core.desempenho import PainelDesempenho, Desempenho
from core.probabilidade_estatistica import ProbabilidadeEstatistica
from indicadores.indicadores import calcular_volatilidade
from core.gestores.martingale_inteligente import MartingaleInteligente
from core.gestores.martingale_tradicional import MartingaleTradicional


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
        self.desempenho = Desempenho(
            config.get("stake_base"), "desempenho.json")

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

    async def _validar_resposta_contrato(self, resposta):
        if not isinstance(resposta, dict):
            return False, "resposta_invalida"
        status = resposta.get("resultado")
        payout = resposta.get("payout")
        contrato_id = resposta.get("contract_id", None)
        status_validos = ["win", "loss"]
        status_ignorados = ["sold", "expired", "cancelled"]
        if status in status_ignorados:
            print(
                f"ℹ️ Contrato encerrado com status '{status}' — operação ignorada.")
            return False, "status_ignorado"
        if not isinstance(payout, (int, float)) or payout < 0:
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

    async def _executar_operacao(self, tipo, stake, padrao):
        # ✅ CORREÇÃO: Lógica de Loss Virtual movida para o início do método
        if self.loss_virtual_ativa:
            resultado_simulado = random.choice(["win", "loss"])
            if resultado_simulado == "loss":
                self.contador_loss_virtual += 1
            else:
                self.contador_loss_virtual = 0

            print(
                f"🧪 Contador de Loss Virtual: {self.contador_loss_virtual}/{self.limite_loss_virtual}")

            if self.contador_loss_virtual < self.limite_loss_virtual:
                print("👻 Ainda em Loss Virtual — operação real será ignorada.")
                await self._finalizar_operacao(resultado_simulado, stake, padrao)
                return True

        # ✅ CORREÇÃO: Lógica de simulação real ou ordem real
        if self.config.get("modo_simulacao", False):
            resultado = random.choice(["win", "loss"])
            payout = stake * \
                random.uniform(1.7, 1.95) if resultado == "win" else 0.0
            resposta = {
                "resultado": resultado,
                "payout": payout,
                "stake": stake,
                "simulacao": True,
                "direcao": tipo,
                "padrao": padrao
            }
        else:
            print("⚡ Escudo de Loss Virtual desativado — operação real será executada.")
            resposta = await self.executor.enviar_ordem(tipo, stake)
            valido, motivo = await self._validar_resposta_contrato(resposta)

            # ✅ CORREÇÃO: Se a resposta não for válida, imprime o aviso e retorna False para continuar a operação.
            if not valido:
                print(f"⚠️ AVISO: Operação ignorada devido a '{motivo}'.")
                return False

        # ✅ CORREÇÃO: Chama o método para finalizar a operação, agora que tudo foi validado
        await self._finalizar_operacao(resposta["resultado"], stake, padrao)

        return True

    async def _finalizar_operacao(self, resultado, stake, padrao):
        """Finaliza a operação, registra o resultado e atualiza as estatísticas."""
        self.desempenho.registrar_resultado(resultado, stake)
        self.gestor.registrar_resultado(resultado)

        if padrao:
            self.estatistica.registrar_operacao(padrao, resultado)

        # Log geral da operação
        self.logger.log("INFO", f"Operação finalizada | Resultado: {resultado.upper()} | Padrão: {padrao} | Stake: {stake:.2f}")

        # Mantém histórico de resultados
        self.sequencia_resultados.append(resultado)
        if len(self.sequencia_resultados) > 5:
            self.sequencia_resultados.pop(0)

        etapa = getattr(self.gestor, "contador", getattr(self.gestor, "etapa", 1))
        self.logger.log("INFO", f"Gestor: {self.config.get('gestor')} | Etapa: {etapa}")
        self.logger.log("INFO", f"Últimos resultados: {' → '.join(self.sequencia_resultados)}")

        if padrao:
            taxa = self.estatistica.calcular_taxa_acerto(padrao)
            self.logger.log("INFO", f"Taxa de acerto para '{padrao}': {taxa}%")

        # Registro da operação em CSV
        self.logger.registrar_operacao(
            tipo=padrao if padrao else "N/A",
            price=self.prices[-1] if self.prices else 0,
            rsi=self.config.get("rsi_valor"),
            lower=self.config.get("bb_inferior"),
            upper=self.config.get("bb_superior"),
            stake=stake
        )

        """Finaliza a operação, registra o resultado e atualiza as estatísticas."""
        self.desempenho.registrar_resultado(resultado, stake)
        self.gestor.registrar_resultado(resultado)

        if padrao:
            self.estatistica.registrar_operacao(padrao, resultado)

        print(
            f"💰 Operação finalizada! Resultado: {resultado.upper()} | Padrão: {padrao} | Stake: {stake:.2f}")

        # ✅ ADIÇÃO: Lógica de log e painel movida para cá
        self.sequencia_resultados.append(resultado)
        if len(self.sequencia_resultados) > 5:
            self.sequencia_resultados.pop(0)

        etapa = getattr(self.gestor, "contador",
                        getattr(self.gestor, "etapa", 1))
        print(f"📊 Gestor: {self.config.get('gestor')} | Etapa: {etapa}")
        print(f"📉 Últimos resultados: {' → '.join(self.sequencia_resultados)}")
        if padrao:
            taxa = self.estatistica.calcular_taxa_acerto(padrao)
            print(f"📈 Taxa de acerto para '{padrao}': {taxa}%")

    async def _processar_tick(self, data):
        """Processa um tick e decide se deve operar."""
        price = data["price"]
        self.prices.append(price)
        if len(self.prices) > 60:
            self.prices.pop(0)

        volatilidade = calcular_volatilidade(self.prices)
        limiar_volatilidade = float(self.config.get("limiar_volatilidade", 0.0005))
        decisao = self.estrategia.decidir(self.prices, volatilidade, limiar_volatilidade)

        if not isinstance(decisao, (list, tuple)):
            self.logger.log("WARNING", f"Estratégia retornou um valor inesperado: {decisao}")
            return

        tipo = decisao[0] if len(decisao) > 0 else None
        padrao = decisao[-1] if len(decisao) > 0 else None

        if tipo is None:
            return

        stake = self.gestor.get_stake()
        self.logger.log("INFO", f"Sinal detectado: {tipo} | Stake: {stake:.2f}")

        try:
            await self._executar_operacao(tipo, stake, padrao)
        except Exception as e:
            self.logger.log("ERROR", f"Falha na execução da ordem ({e}).")
            await asyncio.sleep(5)
            await self._reconectar_websocket()

            """Processa um tick e decide se deve operar."""
            price = data["price"]
            self.prices.append(price)
            if len(self.prices) > 60:
                self.prices.pop(0)

            volatilidade = calcular_volatilidade(self.prices)
            limiar_volatilidade = float(
                self.config.get("limiar_volatilidade", 0.0005))
            decisao = self.estrategia.decidir(
                self.prices, volatilidade, limiar_volatilidade)

            if not isinstance(decisao, (list, tuple)):
                print("⚠️ Estratégia retornou um valor inesperado:", decisao)
                return

            tipo = decisao[0] if len(decisao) > 0 else None
            padrao = decisao[-1] if len(decisao) > 0 else None

            if tipo is None:
                return

            stake = self.gestor.get_stake()
            print(f"🔔 Sinal detectado: {tipo} | 💰 Stake: {stake:.2f}")

            try:
                # ✅ CORREÇÃO: Apenas chama a execução, sem a lógica repetida
                await self._executar_operacao(tipo, stake, padrao)
            except Exception as e:
                print(f"🔌 Falha na execução da ordem ({e}).")
                await asyncio.sleep(5)
                await self._reconectar_websocket()

    async def _reconectar_websocket(self):
        print("🔄 Reconectando...")
        while True:
            try:
                # pequena pausa antes de tentar reconectar
                await asyncio.sleep(5)

                # reconecta ao servidor e reautentica
                await self.mercado.conectar()
                await self.mercado.autenticar(self.token)
                await self.mercado.subscrever_ticks(self.config.get("volatility_index"))

                # atualiza referências de websocket nos módulos dependentes
                if self.executor:
                    self.executor.ws = self.mercado.ws
                if self.saldo:
                    self.saldo.ws = self.mercado.ws

                print("🔄 Reconexão concluída. Retomando operações...")
                break  # sai do loop quando reconectar com sucesso

            except Exception as e:
                print(f"⚠️ Falha na reconexão: {e}. Tentando novamente em 15 segundos...")
                await asyncio.sleep(15)


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
        saldo = Saldo(mercado.ws)

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
                try:
                    await self.mercado.conectar(account_id=self.config.get("account_id"))

                    if not await self.mercado.autenticar(self.token):
                        self.logger.log("ERROR", "Falha na autenticação com Deriv. Verifique o PAT.")
                        await asyncio.sleep(15)
                        continue

                    await self.mercado.subscrever_ticks(self.config.get("volatility_index"))
                    ticks_iniciais = await self.mercado.carregar_ticks_iniciais(
                        self.config.get("volatility_index"), count=100
                    )
                    for preco in ticks_iniciais:
                        self.mercado.precos.append(preco)
                        self.prices.append(preco)

                    self.logger.log("INFO", f"{len(ticks_iniciais)} ticks históricos carregados para inicialização.")

                    # ✅ Só depois de carregar históricos, inicia o loop de manutenção
                    asyncio.create_task(self.mercado.manter_conexao(account_id=self.config.get("account_id")))

                    # ✅ Registrar handler para ticks
                    async def tick_handler(data):
                        tick = self.mercado.processar_tick(data)  # passa dict direto
                        if tick:
                            await self._processar_tick(tick)

                    self.mercado.registrar_handler(tick_handler)

                    # Inicializa executor e saldo (agora com mercado)
                    self.executor = Executor(
                        self.mercado.ws,
                        self.config.get("volatility_index"),
                        float(self.config.get("stake_base")),
                        self.mercado   # ✅ adiciona mercado
                    )
                    self.saldo = Saldo(self.mercado.ws)
                    saldo_inicial = await self.saldo.consultar()
                    self.painel = PainelDesempenho(saldo_inicial)

                    self.logger.log("INFO", f"Bot iniciado para {self.config.get('volatility_index')} | Saldo inicial: {saldo_inicial:.2f}")
                    if self.config.get("modo_simulacao", False):
                        self.logger.log("INFO", "BOT INICIADO EM MODO SIMULAÇÃO — Nenhuma ordem real será enviada!")
                    else:
                        self.logger.log("INFO", "BOT INICIADO EM MODO REAL — Ordens reais serão enviadas!")

                    # Loop principal de operação (sem recv direto!)
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
                                self.logger.log("INFO", "Fora da janela de operação. Aguardando...")
                                await asyncio.sleep(60)
                                continue

                        # ✅ Não consome mais recv — ticks vêm via tick_handler
                        await asyncio.sleep(1)

                except Exception as e:
                    self.logger.log("ERROR", f"Erro crítico no iniciar: {e}")
                    await asyncio.sleep(15)
                    continue

                finally:
                    self.logger.log("INFO", "Fechando bot. Salvando estatísticas...")
                    if hasattr(self, 'estatistica'):
                        self.estatistica.salvar_estatisticas()
                    self.logger.log("INFO", "Bot encerrado.")

                    try:
                        app_id = os.getenv("APP_ID", "1089")
                        self.logger.log("INFO", f"Conectando ao servidor da Deriv (App ID: {app_id})...")

                        # Inicializa mercado e conecta
                        self.mercado = Mercado(
                            url="https://api.derivws.com/trading/v1/options/ws/public",
                            token=self.token,
                            volatility_index=self.config.get("volatility_index")
                        )

                        while True:
                            try:
                                await self.mercado.conectar(account_id=self.config.get("account_id"))

                                if not await self.mercado.autenticar(self.token):
                                    self.logger.log("ERROR", "Falha na autenticação com Deriv. Verifique o PAT.")
                                    await asyncio.sleep(15)
                                    continue

                                await self.mercado.subscrever_ticks(self.config.get("volatility_index"))
                                ticks_iniciais = await self.mercado.carregar_ticks_iniciais(
                                    self.config.get("volatility_index"), count=100
                                )
                                for preco in ticks_iniciais:
                                    self.mercado.precos.append(preco)
                                    self.prices.append(preco)

                                self.logger.log("INFO", f"{len(ticks_iniciais)} ticks históricos carregados para inicialização.")

                                # ✅ Correção: passar account_id ao manter_conexao
                                asyncio.create_task(self.mercado.manter_conexao(account_id=self.config.get("account_id")))

                                # ✅ Registrar handler para ticks
                                async def tick_handler(data):
                                    tick = self.mercado.processar_tick(data)
                                    if tick:
                                        await self._processar_tick(tick)

                                self.mercado.registrar_handler(tick_handler)

                                # Inicializa executor e saldo (agora com mercado)
                                self.executor = Executor(
                                    self.mercado.ws,
                                    self.config.get("volatility_index"),
                                    float(self.config.get("stake_base")),
                                    self.mercado
                                )
                                self.saldo = Saldo(self.mercado.ws)
                                saldo_inicial = await self.saldo.consultar()
                                self.painel = PainelDesempenho(saldo_inicial)

                                self.logger.log("INFO", f"Bot iniciado para {self.config.get('volatility_index')} | Saldo inicial: {saldo_inicial:.2f}")
                                if self.config.get("modo_simulacao", False):
                                    self.logger.log("INFO", "BOT INICIADO EM MODO SIMULAÇÃO — Nenhuma ordem real será enviada!")
                                else:
                                    self.logger.log("INFO", "BOT INICIADO EM MODO REAL — Ordens reais serão enviadas!")

                                # Loop principal de operação (sem recv direto!)
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
                                            self.logger.log("INFO", "Fora da janela de operação. Aguardando...")
                                            await asyncio.sleep(60)
                                            continue

                                    # ✅ Não consome mais recv — ticks vêm via tick_handler
                                    await asyncio.sleep(1)

                            except Exception as e:
                                self.logger.log("ERROR", f"Erro crítico no iniciar: {e}")
                                await asyncio.sleep(15)
                                continue

                    finally:
                        self.logger.log("INFO", "Fechando bot. Salvando estatísticas...")
                        if hasattr(self, 'estatistica'):
                            self.estatistica.salvar_estatisticas()
                        self.logger.log("INFO", "Bot encerrado.")

                        try:
                            app_id = os.getenv("APP_ID", "1089")
                            self.logger.log("INFO", f"Conectando ao servidor da Deriv (App ID: {app_id})...")

                            # Inicializa mercado e conecta
                            self.mercado = Mercado(
                                url="https://api.derivws.com/trading/v1/options/ws/public",
                                token=self.token,
                                volatility_index=self.config.get("volatility_index")
                            )

                            while True:
                                try:
                                    await self.mercado.conectar(account_id=self.config.get("account_id"))

                                    if not await self.mercado.autenticar(self.token):
                                        self.logger.log("ERROR", "Falha na autenticação com Deriv. Verifique o PAT.")
                                        await asyncio.sleep(15)
                                        continue

                                    await self.mercado.subscrever_ticks(self.config.get("volatility_index"))
                                    ticks_iniciais = await self.mercado.carregar_ticks_iniciais(
                                        self.config.get("volatility_index"), count=100
                                    )
                                    for preco in ticks_iniciais:
                                        self.mercado.precos.append(preco)
                                        self.prices.append(preco)

                                    self.logger.log("INFO", f"{len(ticks_iniciais)} ticks históricos carregados para inicialização.")

                                    # ✅ Correção: passar account_id ao manter_conexao
                                    asyncio.create_task(self.mercado.manter_conexao(account_id=self.config.get("account_id")))

                                    # ✅ Registrar handler para ticks
                                    async def tick_handler(data):
                                        tick = self.mercado.processar_tick(json.dumps(data))
                                        if tick:
                                            await self._processar_tick(tick)

                                    self.mercado.registrar_handler(tick_handler)

                                    # Inicializa executor e saldo
                                    self.executor = Executor(
                                        self.mercado.ws,
                                        self.config.get("volatility_index"),
                                        float(self.config.get("stake_base"))
                                    )
                                    self.saldo = Saldo(self.mercado.ws)
                                    saldo_inicial = await self.saldo.consultar()
                                    self.painel = PainelDesempenho(saldo_inicial)

                                    self.logger.log("INFO", f"Bot iniciado para {self.config.get('volatility_index')} | Saldo inicial: {saldo_inicial:.2f}")
                                    if self.config.get("modo_simulacao", False):
                                        self.logger.log("INFO", "BOT INICIADO EM MODO SIMULAÇÃO — Nenhuma ordem real será enviada!")
                                    else:
                                        self.logger.log("INFO", "BOT INICIADO EM MODO REAL — Ordens reais serão enviadas!")

                                    # Loop principal de operação (sem recv direto!)
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
                                                self.logger.log("INFO", "Fora da janela de operação. Aguardando...")
                                                await asyncio.sleep(60)
                                                continue

                                        # ✅ Não consome mais recv — ticks vêm via tick_handler
                                        await asyncio.sleep(1)

                                except Exception as e:
                                    self.logger.log("ERROR", f"Erro crítico no iniciar: {e}")
                                    await asyncio.sleep(15)
                                    continue

                        finally:
                            self.logger.log("INFO", "Fechando bot. Salvando estatísticas...")
                            if hasattr(self, 'estatistica'):
                                self.estatistica.salvar_estatisticas()
                            self.logger.log("INFO", "Bot encerrado.")

                            try:
                                app_id = os.getenv("APP_ID", "1089")
                                self.logger.log("INFO", f"Conectando ao servidor da Deriv (App ID: {app_id})...")

                                # Inicializa mercado e conecta
                                self.mercado = Mercado(
                                    url="https://api.derivws.com/trading/v1/options/ws/public",
                                    token=self.token,
                                    volatility_index=self.config.get("volatility_index")
                                )

                                while True:
                                    try:
                                        await self.mercado.conectar(account_id=self.config.get("account_id"))

                                        if not await self.mercado.autenticar(self.token):
                                            self.logger.log("ERROR", "Falha na autenticação com Deriv. Verifique o PAT.")
                                            await asyncio.sleep(15)
                                            continue

                                        await self.mercado.subscrever_ticks(self.config.get("volatility_index"))
                                        ticks_iniciais = await self.mercado.carregar_ticks_iniciais(
                                            self.config.get("volatility_index"), count=100
                                        )
                                        for preco in ticks_iniciais:
                                            self.mercado.precos.append(preco)
                                            self.prices.append(preco)

                                        self.logger.log("INFO", f"{len(ticks_iniciais)} ticks históricos carregados para inicialização.")

                                        # ✅ Correção: passar account_id ao manter_conexao
                                        asyncio.create_task(self.mercado.manter_conexao(account_id=self.config.get("account_id")))

                                        # ✅ Registrar handler para ticks
                                        async def tick_handler(data):
                                            tick = self.mercado.processar_tick(json.dumps(data))
                                            if tick:
                                                await self._processar_tick(tick)

                                        self.mercado.registrar_handler(tick_handler)

                                        # Inicializa executor e saldo
                                        self.executor = Executor(
                                            self.mercado.ws,
                                            self.config.get("volatility_index"),
                                            float(self.config.get("stake_base"))
                                        )
                                        self.saldo = Saldo(self.mercado.ws)
                                        saldo_inicial = await self.saldo.consultar()
                                        self.painel = PainelDesempenho(saldo_inicial)

                                        self.logger.log("INFO", f"Bot iniciado para {self.config.get('volatility_index')} | Saldo inicial: {saldo_inicial:.2f}")
                                        if self.config.get("modo_simulacao", False):
                                            self.logger.log("INFO", "BOT INICIADO EM MODO SIMULAÇÃO — Nenhuma ordem real será enviada!")
                                        else:
                                            self.logger.log("INFO", "BOT INICIADO EM MODO REAL — Ordens reais serão enviadas!")

                                        # Loop principal de operação (sem recv direto!)
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
                                                    self.logger.log("INFO", "Fora da janela de operação. Aguardando...")
                                                    await asyncio.sleep(60)
                                                    continue

                                            # ✅ Não consome mais recv — ticks vêm via tick_handler
                                            await asyncio.sleep(1)

                                    except Exception as e:
                                        self.logger.log("ERROR", f"Erro crítico no iniciar: {e}")
                                        await asyncio.sleep(15)
                                        continue

                            finally:
                                self.logger.log("INFO", "Fechando bot. Salvando estatísticas...")
                                if hasattr(self, 'estatistica'):
                                    self.estatistica.salvar_estatisticas()
                                self.logger.log("INFO", "Bot encerrado.")

                                try:
                                    app_id = os.getenv("APP_ID", "1089")
                                    self.logger.log("INFO", f"Conectando ao servidor da Deriv (App ID: {app_id})...")

                                    # Inicializa mercado e conecta
                                    self.mercado = Mercado(
                                        url="https://api.derivws.com/trading/v1/options/ws/public",
                                        token=self.token,
                                        volatility_index=self.config.get("volatility_index")
                                    )

                                    while True:
                                        try:
                                            await self.mercado.conectar(account_id=self.config.get("account_id"))

                                            if not await self.mercado.autenticar(self.token):
                                                self.logger.log("ERROR", "Falha na autenticação com Deriv. Verifique o PAT.")
                                                await asyncio.sleep(15)
                                                continue

                                            await self.mercado.subscrever_ticks(self.config.get("volatility_index"))
                                            ticks_iniciais = await self.mercado.carregar_ticks_iniciais(
                                                self.config.get("volatility_index"), count=100
                                            )
                                            for preco in ticks_iniciais:
                                                self.mercado.precos.append(preco)
                                                self.prices.append(preco)

                                            self.logger.log("INFO", f"{len(ticks_iniciais)} ticks históricos carregados para inicialização.")

                                            # ✅ Correção: passar account_id ao manter_conexao
                                            asyncio.create_task(self.mercado.manter_conexao(account_id=self.config.get("account_id")))

                                            # ✅ Registrar handler para ticks
                                            async def tick_handler(data):
                                                tick = self.mercado.processar_tick(json.dumps(data))
                                                if tick:
                                                    await self._processar_tick(tick)

                                            self.mercado.registrar_handler(tick_handler)

                                            # Inicializa executor e saldo
                                            self.executor = Executor(
                                                self.mercado.ws,
                                                self.config.get("volatility_index"),
                                                float(self.config.get("stake_base"))
                                            )
                                            self.saldo = Saldo(self.mercado.ws)
                                            saldo_inicial = await self.saldo.consultar()
                                            self.painel = PainelDesempenho(saldo_inicial)

                                            self.logger.log("INFO", f"Bot iniciado para {self.config.get('volatility_index')} | Saldo inicial: {saldo_inicial:.2f}")
                                            if self.config.get("modo_simulacao", False):
                                                self.logger.log("INFO", "BOT INICIADO EM MODO SIMULAÇÃO — Nenhuma ordem real será enviada!")
                                            else:
                                                self.logger.log("INFO", "BOT INICIADO EM MODO REAL — Ordens reais serão enviadas!")

                                            # Loop principal de operação (sem recv direto!)
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
                                                        self.logger.log("INFO", "Fora da janela de operação. Aguardando...")
                                                        await asyncio.sleep(60)
                                                        continue

                                                await asyncio.sleep(1)  # ✅ agora o loop só espera, ticks vêm via handler

                                        except Exception as e:
                                            self.logger.log("ERROR", f"Erro crítico no iniciar: {e}")
                                            await asyncio.sleep(15)
                                            continue

                                finally:
                                    self.logger.log("INFO", "Fechando bot. Salvando estatísticas...")
                                    if hasattr(self, 'estatistica'):
                                        self.estatistica.salvar_estatisticas()
                                    self.logger.log("INFO", "Bot encerrado.")

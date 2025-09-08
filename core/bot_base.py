import asyncio
from core.mercado import Mercado
from core.executor import Executor
from core.logger import Logger
from core.soros import GerenciadorSoros
from core.saldo import Saldo
from core.desempenho import PainelDesempenho
from estrategias.martingale_inteligente import MartingaleInteligente
from core.probabilidade_estatistica import ProbabilidadeEstatistica

class BotBase:
    def __init__(self, config, token, estrategia):
        self.config = config
        self.token = token
        self.estrategia = estrategia
        self.modo_simulacao = config.get("modo_simulacao", False)
        self.prices = []
        self.loss_count = 0
        self.profit_count = 0

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
            try:
                msg = await mercado.ws.recv()
            except Exception as e:
                print(f"⚠️ Erro na conexão: {e}")
                await mercado.conectar()
                await mercado.autenticar(self.token)
                await mercado.subscrever_ticks(self.config["volatility_index"])
                continue

            data = mercado.processar_tick(msg)
            if not data:
                continue

            price = data["price"]
            print("🔄 Loop ativo | Preço atual:", price)
            self.prices.append(price)

            if hasattr(self.estrategia, "tipo") and self.estrategia.tipo == "price_action":

                candles = self.gerar_candles()
                tipo, rsi, lower, upper, padrao = self.estrategia.decidir(candles)
                print(f"📊 Price Action detectado: {padrao}")
            else:
                tipo, rsi, lower, upper, padrao = self.estrategia.decidir(self.prices)

            if tipo is None:
                print("⏳ Nenhum sinal gerado. Aguardando próximo tick.")
                continue

            saldo_atual = await saldo.consultar()

            stake_soros = soros.get_stake(saldo_atual)
            stake = martingale.get_stake()

            print(f"🔔 Sinal detectado: {tipo} | 💰 Stake: {stake:.2f}")

            if self.modo_simulacao:
                import random
                resultado = random.choice(["win", "loss"])
                print(f"🧪 Simulação ativa | Resultado: {resultado}")
            else:
                resultado = await executor.enviar_ordem(tipo, stake)

            print(f"📊 Resultado: {resultado}")

            if resultado in ["win", "loss"]:
                painel.registrar_operacao(saldo_atual, resultado, stake, tipo)
                soros.registrar_resultado(resultado)
                martingale.registrar_resultado(resultado)
                estatistica.registrar_operacao(tipo, resultado, padrao)
                taxa = estatistica.calcular_taxa_acerto(padrao)
                print(f"📈 Taxa de acerto para '{padrao}': {taxa}%")
                logger.registrar(tipo, price, rsi, lower, upper, stake)

                self.loss_count += resultado == "loss"
                self.profit_count += resultado == "win"

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
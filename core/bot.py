import asyncio
from core.mercado import Mercado
from core.estrategia import Estrategia
from core.executor import Executor
from core.logger import Logger
from core.soros import GerenciadorSoros
from core.saldo import Saldo
from core.desempenho import PainelDesempenho
class Bot:
    def __init__(self, config, token):
        self.config = config
        self.token = token
        self.prices = []
        self.loss_count = 0
        self.profit_count = 0

    async def iniciar(self):
        mercado = Mercado("wss://ws.derivws.com/websockets/v3?app_id=1089", self.token, self.config["volatility_index"])
        await mercado.conectar()
        if not await mercado.autenticar(self.token):
            return

        await mercado.subscrever_ticks(self.config["volatility_index"])
        asyncio.create_task(mercado.manter_conexao())
        
        if self.config["estrategia"] == "rsi_bollinger":
         from core.estrategia_rsi import EstrategiaRSI
         estrategia = EstrategiaRSI(self.config["rsi_period"], self.config["bollinger_period"])
        elif self.config["estrategia"] == "media_movel":
            from core.estrategia_mm import EstrategiaMM
            estrategia = EstrategiaMM(self.config["mm_periodo_curto"], self.config["mm_periodo_longo"])
        else:
            raise ValueError(f"Estratégia desconhecida: {self.config['estrategia']}")

        estrategia = Estrategia(self.config["rsi_period"], self.config["bollinger_period"])
        executor = Executor(mercado.ws, self.config["volatility_index"], self.config["stake"])
        logger = Logger()
        saldo = Saldo(mercado.ws)

        saldo_inicial = await saldo.consultar()
        painel = PainelDesempenho(saldo_inicial)
        meta_lucro = saldo_inicial * self.config.get("meta_lucro_percentual", 0.10)
        stop_loss = saldo_inicial * self.config.get("stop_loss_percentual", 0.05)

        stake_base = max(round(saldo_inicial * 0.01, 2), 0.35)
        soros = GerenciadorSoros(stake_base, max_etapas=2)

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

            if len(self.prices) >= self.config["bollinger_period"]:
                tipo, rsi, lower, upper = estrategia.decidir(self.prices)
                print(f"💹 Preço: {price:.2f} | RSI: {rsi:.2f} | BB: [{lower:.2f}, {upper:.2f}]")

                if tipo is not None:
                    saldo_atual = await saldo.consultar()
                    prejuizo_total = saldo_atual - saldo_inicial

                    if prejuizo_total < 0:
                        stake = soros.calcular_stake_recuperacao(abs(prejuizo_total), payout=0.95)
                        print(f"🔁 Recuperando prejuízo: {prejuizo_total:.2f} | Stake ajustada: {stake:.2f}")
                    else:
                        stake = soros.get_stake(saldo_atual)

                    print(f"🔔 Sinal detectado: {tipo} | 💰 Stake: {stake:.2f}")
                    resultado = await executor.enviar_ordem(tipo, stake)
                    print(f"📊 Resultado recebido: {resultado}")

                    if resultado in ["win", "loss"]:

                        painel.registrar_operacao(
                        saldo_atual=saldo_atual,
                        resultado=resultado,
                        stake=stake,
                        tipo=tipo
                         )

                        soros.registrar_resultado(resultado)
                        print(f"🔁 Soros etapa: {soros.etapa} | Próxima stake: {soros.stake_atual:.2f}")
                        logger.registrar(tipo, price, rsi, lower, upper, stake)
                        
                        if resultado == "loss":
                            self.loss_count += 1
                            operacoes_realizadas = self.loss_count + self.profit_count

                            if operacoes_realizadas >= self.config.get("max_operacoes", 20):
                                print("⏸️ Limite de operações atingido. Pausando o bot.")
                                break
                            if self.loss_count >= 3:
                                soros.reduzir_stake(fator=0.5)
                                print("⚠️ Reduzindo stake após sequência de perdas.")
                        elif resultado == "win":
                            self.profit_count += 1

                        operacoes_realizadas = self.loss_count + self.profit_count
                        if operacoes_realizadas >= self.config.get("max_operacoes", 20):
                            print("⏸️ Limite de operações atingido. Encerrando.")
                            break

                        saldo_atual = await saldo.consultar()
                        lucro_total = saldo_atual - saldo_inicial

                        if lucro_total >= meta_lucro:
                            print("🎯 Meta de lucro atingida. Encerrando.")
                            break

                        if lucro_total <= -stop_loss:
                            print("🛑 Stop loss atingido. Encerrando.")
                            break

                        await asyncio.sleep(10)
                    else:
                        print("⚠️ Resultado inválido ou erro na operação. Continuando...")

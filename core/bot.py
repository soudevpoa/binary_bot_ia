import asyncio
from core.mercado import Mercado
from core.estrategia import Estrategia
from core.executor import Executor
from core.logger import Logger
from core.soros import GerenciadorSoros
from core.saldo import Saldo
import websockets

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
        # ✅ Consulta saldo inicial e define stake base
        saldo = Saldo(mercado.ws)
        saldo_atual = await saldo.consultar()
        stake_base = round(saldo_atual * 0.01, 2)
        soros = GerenciadorSoros(stake_base, max_etapas=2)


        estrategia = Estrategia(self.config["rsi_period"], self.config["bollinger_period"])
        executor = Executor(mercado.ws, self.config["volatility_index"], self.config["stake"])
        logger = Logger()
        soros = GerenciadorSoros(self.config["stake"], max_etapas=2)

        print(f"📡 Bot iniciado para {self.config['volatility_index']}")

        while True:
            try:
                msg = await mercado.ws.recv()
            except websockets.ConnectionClosedError:
                print("⚠️ Conexão encerrada inesperadamente. Tentando reconectar...")
                await mercado.conectar()
                if not await mercado.autenticar(self.token):
                    print("❌ Falha na autenticação após reconexão.")
                    break
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
                    saldo = Saldo(mercado.ws)
                    saldo_atual = await saldo.consultar()
                    stake = soros.get_stake(saldo=saldo_atual)

                    print(f"🔔 Sinal detectado: {tipo} | 💰 Stake: {stake:.2f}")
                    resultado = await executor.enviar_ordem(tipo, stake)
                    print(f"📊 Resultado recebido: {resultado}")

                    if resultado in ["win", "loss"]:
                        soros.registrar_resultado(resultado)
                        print(f"🔁 Soros etapa: {soros.etapa} | Próxima stake: {soros.stake_atual:.2f}")

                        logger.registrar(tipo, price, rsi, lower, upper, stake)

                        if resultado == "loss":
                            self.loss_count += 1
                        elif resultado == "win":
                            self.profit_count += 1

                        await asyncio.sleep(10)
                    else:
                        print("⚠️ Resultado inválido ou erro na operação. Continuando...")

                # Verificação de limites de risco (fora do bloco de resultado)
                if self.loss_count >= self.config.get("loss_limit", 5):
                    print("⚠️ Limite de perdas atingido. Encerrando.")
                    break

                if self.profit_count >= self.config.get("profit_target", 10):
                    print("🎯 Meta de lucro atingida. Encerrando.")
                    break
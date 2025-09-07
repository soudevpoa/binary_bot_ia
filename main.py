import asyncio
from config_loader import carregar_config
from core.bot_base import BotBase
from bots.bot_rsi import iniciar_bot_rsi
from bots.bot_price_action import iniciar_bot_price_action
from bots.bot_reversao import iniciar_bot_reversao
from estrategias.bollinger_volatilidade import EstrategiaBollingerVolatilidade

config = carregar_config("config.json")
token = config["token"]

if config["estrategia"] == "rsi_bollinger":
    bot = iniciar_bot_rsi(config, token)

elif config["estrategia"] == "price_action":
    bot = iniciar_bot_price_action(config, token)

elif config["estrategia"] == "reversao_tendencia":
    bot = iniciar_bot_reversao(config, token)

elif config["estrategia"] == "bollinger_volatilidade":
    estrategia = EstrategiaBollingerVolatilidade(
        periodo=config["periodo"],
        desvio=config["desvio"],
        limiar_volatilidade=config["limiar_volatilidade"]
    )
    bot = BotBase(config, token, estrategia)

asyncio.run(bot.iniciar())
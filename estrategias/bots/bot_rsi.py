from bots.bot_rsi import iniciar_bot_rsi
from bots.bot_price_action import iniciar_bot_price_action
# ... outros bots

config = carregar_config("config.json")
token = config["token"]

if config["estrategia"] == "rsi_bollinger":
    bot = iniciar_bot_rsi(config, token)
elif config["estrategia"] == "price_action":
    bot = iniciar_bot_price_action(config, token)

asyncio.run(bot.iniciar())
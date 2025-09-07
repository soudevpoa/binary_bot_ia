import asyncio
from bots.bot_rsi import iniciar_bot_rsi
from bots.bot_price_action import iniciar_bot_price_action
from config_loader import carregar_config

# Carrega a configuração do bot RSI
config = carregar_config("config_rsi.json")
token = config["token"]

# Inicializa o bot com a estratégia RSI
bot = iniciar_bot_rsi(config, token)

if config["estrategia"] == "price_action":
    bot = iniciar_bot_price_action(config, token)


# Executa o bot
if __name__ == "__main__":
    asyncio.run(bot.iniciar())
import asyncio
import json
from core.bot import Bot

# Carregar configurações
with open("config.json") as f:
    config = json.load(f)

# Carregar token
with open("auth.json") as f:
    auth = json.load(f)

# Iniciar bot
if __name__ == "__main__":
    bot = Bot(config, auth["token"])
    asyncio.run(bot.iniciar())
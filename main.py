import asyncio
from config_loader import carregar_config
from core.bot_base import BotBase
from bots.bot_rsi import iniciar_bot_rsi
from bots.bot_price_action import iniciar_bot_price_action
from bots.bot_reversao import iniciar_bot_reversao
from bots.bot_mm import iniciar_bot_mm
from bots.bot_mm_rsi import iniciar_bot_mm_rsi
import sys
from config_loader import carregar_config  # Certifique-se que esse arquivo existe

# Lê o nome da estratégia como argumento
estrategia_nome = sys.argv[1]  # Ex: "rsi_bollinger"

# Monta o caminho do config correspondente
config_path = f"configs/config_{estrategia_nome}.json"

# Carrega o config específico
config = carregar_config(config_path)

token = config["token"]

if config["estrategia"] == "rsi_bollinger":
    bot = iniciar_bot_rsi(config, token)

elif config["estrategia"] == "price_action":
    bot = iniciar_bot_price_action(config, token)

elif config["estrategia"] == "reversao_tendencia":
    bot = iniciar_bot_reversao(config, token)
    
elif config["estrategia"] == "media_movel":
    bot = iniciar_bot_mm(config, token)

elif config["estrategia"] == "mm_rsi":
    bot = iniciar_bot_mm_rsi(config, token)



elif config["estrategia"] == "bollinger_volatilidade":
    estrategia = EstrategiaBollingerVolatilidade(
        periodo=config["periodo"],
        desvio=config["desvio"],
        limiar_volatilidade=config["limiar_volatilidade"]
    )
    bot = BotBase(config, token, estrategia)

asyncio.run(bot.iniciar())
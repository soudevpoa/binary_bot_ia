# main.py

import asyncio
import os
import sys
from dotenv import load_dotenv
from config_loader import carregar_config
from core.bot_base import BotBase
from bots.bot_rsi import iniciar_bot_rsi
from bots.bot_price_action import iniciar_bot_price_action
from bots.bot_reversao import iniciar_bot_reversao
from bots.bot_mm import iniciar_bot_mm
from bots.bot_mm_rsi import iniciar_bot_mm_rsi

# Carrega variáveis do .env
load_dotenv()

# Lê o nome da estratégia como argumento
estrategia_nome = sys.argv[1]  # Ex: "rsi_bollinger"

# Monta o caminho do config correspondente
config_path = f"configs/config_{estrategia_nome}.json"

# Carrega o config específico
config = carregar_config(config_path)

# Agora o token vem do .env
token = os.getenv("DERIV_API_TOKEN", "").strip()
if not token:
    print("❌ Nenhum token encontrado no .env! Verifique DERIV_API_TOKEN.")
else:
    print(f"🔑 Token carregado (prefixo): {token[:10]}...")

# Seleciona o bot com base no argumento
if estrategia_nome == "rsi_bollinger":
    bot = iniciar_bot_rsi(config, token)

elif estrategia_nome == "price_action":
    bot = iniciar_bot_price_action(config, token)

elif estrategia_nome == "reversao_tendencia":
    bot = iniciar_bot_reversao(config, token)

elif estrategia_nome == "media_movel":
    bot = iniciar_bot_mm(config, token)

elif estrategia_nome == "mm_rsi":
    bot = iniciar_bot_mm_rsi(config, token)

elif estrategia_nome == "bollinger_volatilidade":
    from estrategias.bollinger_volatilidade import EstrategiaBollingerVolatilidade
    estrategia = EstrategiaBollingerVolatilidade(
        periodo=config["periodo"],
        desvio=config["desvio"],
        limiar_volatilidade=config["limiar_volatilidade"]
    )
    bot = BotBase(config, token, estrategia)

# Inicia o bot
asyncio.run(bot.iniciar())

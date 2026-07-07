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

# Valida argumento
if len(sys.argv) < 2:
    print("❌ Informe o nome da estratégia (ex: rsi_bollinger).")
    sys.exit(1)

estrategia_nome = sys.argv[1]
config_path = f"configs/config_{estrategia_nome}.json"
config = carregar_config(config_path)

# Token da API
token = os.getenv("DERIV_API_TOKEN", "").strip()
if not token:
    print("❌ Nenhum token encontrado no .env! Verifique DERIV_API_TOKEN.")
    sys.exit(1)
else:
    print(f"🔑 Token carregado (prefixo): {token[:10]}...")

# Seleção de estratégia
estrategias = {
    "rsi_bollinger": iniciar_bot_rsi,
    "price_action": iniciar_bot_price_action,
    "reversao_tendencia": iniciar_bot_reversao,
    "media_movel": iniciar_bot_mm,
    "mm_rsi": iniciar_bot_mm_rsi
}

if estrategia_nome in estrategias:
    bot = estrategias[estrategia_nome](config, token)
elif estrategia_nome == "bollinger_volatilidade":
    from estrategias.bollinger_volatilidade import EstrategiaBollingerVolatilidade
    estrategia = EstrategiaBollingerVolatilidade(
        periodo=config["periodo"],
        desvio=config["desvio"],
        limiar_volatilidade=config["limiar_volatilidade"]
    )
    bot = BotBase(config, token, estrategia)
else:
    print(f"❌ Estratégia '{estrategia_nome}' não reconhecida.")
    sys.exit(1)

print(f"🚀 Iniciando bot com estratégia: {estrategia_nome}")
asyncio.run(bot.iniciar())

import asyncio
import json
from core.bot_base import BotBase
from estrategias.mm_rsi import EstrategiaMMRSI

async def iniciar_bot_mm_rsi(config, token, estatisticas_file):
    # A função agora recebe os argumentos diretamente.
    # A lógica de carregar o arquivo de configuração foi removida daqui,
    # pois agora ela está centralizada no iniciar_bot.py.
    
    estrategia = EstrategiaMMRSI(
        mm_curto=config["mm_periodo_curto"],
        mm_longo=config["mm_periodo_longo"],
        rsi_period=config["rsi_period"],
        rsi_upper=config["rsi_upper"],
        rsi_lower=config["rsi_lower"]
    )

    bot = BotBase(config, token, estrategia, estatisticas_file)
    
    # Retorna a instância do bot, sem iniciá-lo.
    return bot
import asyncio
import json
from core.bot_base import BotBase
from estrategias.rsi_bollinger import EstrategiaRSI

async def iniciar_bot_rsi(config, token, estatisticas_file):
    # A função agora recebe os argumentos diretamente do iniciar_bot.py.
    # A lógica de carregar o arquivo de configuração foi removida daqui,
    # pois agora ela está centralizada no iniciar_bot.py.

    estrategia = EstrategiaRSI(
        rsi_period=config["rsi_period"],
        bollinger_period=config["bollinger_period"],
        desvio=config["desvio"]
    )
    
    # Instancia o bot de forma correta com os argumentos recebidos
    bot = BotBase(config, token, estrategia, estatisticas_file)
    
    # Retorna a instância do bot, sem iniciá-lo
    return bot
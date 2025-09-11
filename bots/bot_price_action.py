import asyncio
import json
from core.bot_base import BotBase
from estrategias.price_action import EstrategiaPriceAction

async def iniciar_bot_price_action(config, token, estatisticas_file):
    # A função agora recebe os argumentos diretamente.
    # A lógica de carregar o arquivo de configuração foi movida daqui,
    # pois agora ela está centralizada no iniciar_bot.py.

    estrategia = EstrategiaPriceAction()
    
    # Instancia o bot de forma correta com os argumentos recebidos
    bot = BotBase(config, token, estrategia, estatisticas_file)
    
    # Retorna a instância do bot, sem iniciá-lo
    return bot
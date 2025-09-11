from core.bot_base import BotBase
from estrategias.price_action import EstrategiaPriceAction

def iniciar_bot_price_action(config, token,estatisticas_file):
    estrategia = EstrategiaPriceAction()
    bot = BotBase(config, token, estrategia,estatisticas_file)
    return bot
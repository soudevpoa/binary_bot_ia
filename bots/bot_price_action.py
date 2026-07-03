# bots/bot_price_action.py

import asyncio
import json
from core.bot_base import BotBase
from estrategias.price_action import EstrategiaPriceAction

class BotPriceAction(BotBase):
    def __init__(self, config, token, estatisticas_file):
        estrategia = EstrategiaPriceAction()
        super().__init__(config, token, estrategia, estatisticas_file)

# Função de inicialização para ser chamada pelo main.py
def iniciar_bot_price_action(config, token):
    return BotPriceAction(config, token, config.get("estatisticas_file"))

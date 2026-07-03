# bots/bot_rsi.py

import asyncio
import json
from core.bot_base import BotBase
from estrategias.rsi_bollinger import EstrategiaRSI

class BotRSI(BotBase):
    def __init__(self, config, token, estatisticas_file):
        estrategia = EstrategiaRSI(
            rsi_period=config["rsi_period"],
            bollinger_period=config["bollinger_period"],
            desvio=config["desvio"]
        )
        super().__init__(config, token, estrategia, estatisticas_file)

# Função de inicialização para ser chamada pelo main.py
def iniciar_bot_rsi(config, token):
    return BotRSI(config, token, config.get("estatisticas_file"))

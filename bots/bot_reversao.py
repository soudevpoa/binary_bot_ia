# bots/bot_reversao.py

import asyncio
import json
from core.bot_base import BotBase
from estrategias.reversao_tendencia import EstrategiaReversaoTendencia

class BotReversao(BotBase):
    def __init__(self, config, token, estatisticas_file):
        estrategia = EstrategiaReversaoTendencia(config["rsi_period"])
        super().__init__(config, token, estrategia, estatisticas_file)

# Função de inicialização para ser chamada pelo main.py
def iniciar_bot_reversao(config, token):
    return BotReversao(config, token, config.get("estatisticas_file"))

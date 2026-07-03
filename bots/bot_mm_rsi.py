# bots/bot_mm_rsi.py

import asyncio
import json
from core.bot_base import BotBase
from estrategias.mm_rsi import EstrategiaMMRSI

class BotMMRSI(BotBase):
    def __init__(self, config, token, estatisticas_file):
        estrategia = EstrategiaMMRSI(
            mm_curto=config["mm_periodo_curto"],
            mm_longo=config["mm_periodo_longo"],
            rsi_period=config["rsi_period"],
            rsi_upper=config["rsi_upper"],
            rsi_lower=config["rsi_lower"]
        )
        super().__init__(config, token, estrategia, estatisticas_file)

# Função de inicialização para ser chamada pelo main.py
def iniciar_bot_mm_rsi(config, token):
    return BotMMRSI(config, token, config.get("estatisticas_file"))

# No arquivo bots/bot_rsi.py

import asyncio
import json
from core.bot_base import BotBase
from estrategias.rsi_bollinger import EstrategiaRSI

# --- CLASSE DO BOT REAL ---
# Ela herda de BotBase, que cuida da lógica de inicialização, estatísticas, etc.
class BotRSI(BotBase):
    def __init__(self, config, token, estatisticas_file):
        # Instancia a sua estratégia de RSI e Bollinger.
        # Note que ela precisa de três parâmetros da sua configuração.
        estrategia = EstrategiaRSI(
            rsi_period=config["rsi_period"],
            bollinger_period=config["bollinger_period"],
            desvio=config["desvio"]
        )
        
        # Chama o construtor da classe-base (BotBase)
        # e passa a estratégia para ela.
        super().__init__(config, token, estrategia, estatisticas_file)
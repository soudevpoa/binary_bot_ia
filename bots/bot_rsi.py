from core.bot_base import BotBase
from estrategias.rsi_bollinger import EstrategiaRSI

def iniciar_bot_rsi(config, token,estatisticas_file):
    estrategia = EstrategiaRSI(
        rsi_period=config["rsi_period"],
        bollinger_period=config["bollinger_period"],
        desvio=config["desvio"]
    )

    bot = BotBase(config, token, estrategia,estatisticas_file)
    return bot
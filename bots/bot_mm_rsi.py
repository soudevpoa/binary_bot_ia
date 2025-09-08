from core.bot_base import BotBase
from estrategias.mm_rsi import EstrategiaMMRSI

def iniciar_bot_mm_rsi(config, token):
    estrategia = EstrategiaMMRSI(
        mm_curto=config["mm_periodo_curto"],
        mm_longo=config["mm_periodo_longo"],
        rsi_period=config["rsi_period"],
        rsi_upper=config["rsi_upper"],
        rsi_lower=config["rsi_lower"]
    )
    bot = BotBase(config, token, estrategia)
    return bot
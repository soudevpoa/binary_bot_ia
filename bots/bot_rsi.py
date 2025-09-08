from core.bot_base import BotBase
from estrategias.rsi_bollinger import EstrategiaRSI  # Certifica que esse arquivo existe

def iniciar_bot_rsi(config, token):
    estrategia = EstrategiaRSI(
        periodo=config["rsi_period"],
        limite_superior=config["rsi_upper"],
        limite_inferior=config["rsi_lower"]
    )
    bot = BotBase(config, token, estrategia)
    return bot
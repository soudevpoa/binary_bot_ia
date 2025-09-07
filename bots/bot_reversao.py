from core.bot_base import BotBase
from estrategias.reversao_tendencia import EstrategiaReversaoTendencia

def iniciar_bot_reversao(config, token):
    estrategia = EstrategiaReversaoTendencia(config["rsi_period"])
    bot = BotBase(config, token, estrategia)
    return bot
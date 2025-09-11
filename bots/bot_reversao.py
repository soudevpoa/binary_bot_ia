from core.bot_base import BotBase
from estrategias.reversao_tendencia import EstrategiaReversaoTendencia

def iniciar_bot_reversao(config, token,estatisticas_file):
    estrategia = EstrategiaReversaoTendencia(config["rsi_period"])
    bot = BotBase(config, token, estrategia,estatisticas_file)
    return bot
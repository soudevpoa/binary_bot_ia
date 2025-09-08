from core.bot_base import BotBase
from estrategias.media_movel import EstrategiaMediaMovel

def iniciar_bot_mm(config, token):
    estrategia = EstrategiaMediaMovel(
        periodo_curto=config["mm_periodo_curto"],
        periodo_longo=config["mm_periodo_longo"]
    )
    bot = BotBase(config, token, estrategia)
    return bot
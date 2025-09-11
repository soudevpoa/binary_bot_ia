from core.bot_base import BotBase
from estrategias.media_movel import EstrategiaMediaMovel
from core.probabilidade_estatistica import ProbabilidadeEstatistica

def iniciar_bot_mm(config, token,estatisticas_file):
    estrategia = EstrategiaMediaMovel(
        periodo_curto=config["mm_periodo_curto"],
        periodo_longo=config["mm_periodo_longo"]
    )
    bot = BotBase(config, token, estrategia,estatisticas_file)
    return bot
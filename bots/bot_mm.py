# bots/bot_mm.py
from core.bot_base import BotBase
from estrategias.media_movel import EstrategiaMediaMovel

class BotMM(BotBase):
    def __init__(self, config, token, estatisticas_file):
        # Configura a estratégia específica
        estrategia = EstrategiaMediaMovel(
            periodo_curto=config.get("mm_periodo_curto", 10),
            periodo_longo=config.get("mm_periodo_longo", 20)
        )
        # Passa tudo para o BotBase
        super().__init__(config, token, estrategia, estatisticas_file)

    # ✅ O método iniciar() foi removido. 
    # Agora ele usa o do BotBase automaticamente, que já aceita o account_id!
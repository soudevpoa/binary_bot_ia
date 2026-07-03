# bots/bot_mm.py

import json
from core.bot_base import BotBase
from estrategias.media_movel import EstrategiaMediaMovel

class BotMM(BotBase):
    def __init__(self, config, token, estatisticas_file):
        estrategia = EstrategiaMediaMovel(
            periodo_curto=config["mm_periodo_curto"],
            periodo_longo=config["mm_periodo_longo"]
        )
        super().__init__(config, token, estrategia, estatisticas_file)

    async def iniciar(self):
        print(f"📈 Bot MM iniciado com estratégia: {self.estrategia}")
        await super().iniciar()

# Função de inicialização para ser chamada pelo main.py
def iniciar_bot_mm(config, token):
    return BotMM(config, token, config.get("estatisticas_file"))

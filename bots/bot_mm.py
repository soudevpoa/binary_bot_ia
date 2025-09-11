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

async def iniciar_bot_mm(config, token, estatisticas_file):
    # A função agora recebe os argumentos diretamente do iniciar_bot.py
    # Removemos a lógica de carregar o arquivo aqui
    
    # Instancia a classe do bot com os argumentos recebidos
    bot = BotMM(config, token, estatisticas_file)
    
    # Retorna a instância do bot
    return bot
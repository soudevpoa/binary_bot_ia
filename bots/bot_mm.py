from core.bot_base import BotBase
from estrategias.media_movel import EstrategiaMediaMovel
import json

def iniciar_bot_mm():
    # Carrega configurações
    with open("config/config_mm.json", "r") as f:
        config = json.load(f)

    token = config["token"]
    estatisticas_file = config["estatisticas_file"]

    estrategia = EstrategiaMediaMovel(
        periodo_curto=config["mm_periodo_curto"],
        periodo_longo=config["mm_periodo_longo"]
    )

    bot = BotBase(config, token, estrategia, estatisticas_file)
    bot.executar()

if __name__ == "__main__":
    iniciar_bot_mm()

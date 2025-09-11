from core.bot_base import BotBase
from estrategias.mm_rsi import EstrategiaMMRSI
import json

def iniciar_bot_mm_rsi():
    # Carrega configurações
    with open("config/config_mm_rsi.json", "r") as f:
        config = json.load(f)

    token = config["token"]
    estatisticas_file = config["estatisticas_file"]

    estrategia = EstrategiaMMRSI(
        mm_curto=config["mm_periodo_curto"],
        mm_longo=config["mm_periodo_longo"],
        rsi_period=config["rsi_period"],
        rsi_upper=config["rsi_upper"],
        rsi_lower=config["rsi_lower"]
    )

    bot = BotBase(config, token, estrategia, estatisticas_file)
    bot.executar()

if __name__ == "__main__":
    iniciar_bot_mm_rsi()

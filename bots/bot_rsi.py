from core.bot_base import BotBase
from estrategias.rsi_bollinger import EstrategiaRSI
import json

def iniciar_bot_rsi():
    # Carrega configurações
    with open("config/config_rsi.json", "r") as f:
        config = json.load(f)

    token = config["token"]
    estatisticas_file = config["estatisticas_file"]

    estrategia = EstrategiaRSI(
        rsi_period=config["rsi_period"],
        bollinger_period=config["bollinger_period"],
        desvio=config["desvio"]
    )

    bot = BotBase(config, token, estrategia, estatisticas_file)
    bot.executar()

if __name__ == "__main__":
    iniciar_bot_rsi()

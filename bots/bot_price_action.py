from core.bot_base import BotBase
from estrategias.price_action import EstrategiaPriceAction
import json

def iniciar_bot_price_action():
    # Carrega configurações
    with open("config/config_price_action.json", "r") as f:
        config = json.load(f)

    token = config["token"]
    estatisticas_file = config["estatisticas_file"]

    estrategia = EstrategiaPriceAction()
    bot = BotBase(config, token, estrategia, estatisticas_file)
    bot.executar()

if __name__ == "__main__":
    iniciar_bot_price_action()

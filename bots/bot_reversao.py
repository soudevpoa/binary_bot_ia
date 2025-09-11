from core.bot_base import BotBase
from estrategias.reversao_tendencia import EstrategiaReversaoTendencia
import json

def iniciar_bot_reversao():
    # Carrega configurações
    with open("config/config_reversao.json", "r") as f:
        config = json.load(f)

    token = config["token"]
    estatisticas_file = config["estatisticas_file"]

    estrategia = EstrategiaReversaoTendencia(config["rsi_period"])
    bot = BotBase(config, token, estrategia, estatisticas_file)
    bot.executar()

if __name__ == "__main__":
    iniciar_bot_reversao()

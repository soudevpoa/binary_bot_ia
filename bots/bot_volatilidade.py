from core.bot_base import BotBase
from estrategias.bollinger_volatilidade import EstrategiaBollingerVolatilidade

def iniciar_bot_volatilidade(config, token):
    estrategia = EstrategiaBollingerVolatilidade(
        periodo=config["periodo"],
        desvio=config["desvio"],
        limiar_volatilidade=config["limiar_volatilidade"]
    )
    bot = BotBase(config, token, estrategia)
    return bot
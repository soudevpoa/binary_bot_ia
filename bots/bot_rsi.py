from core.bot_base import BotBase
from estrategias.bollinger_volatilidade import EstrategiaBollingerVolatilidade

def iniciar_bot_rsi(config, token):
    estrategia = EstrategiaBollingerVolatilidade(
        periodo=config["bollinger_period"],
        desvio=2,
        limiar_volatilidade=config["limiar_volatilidade"]
    )
    bot = BotBase(config, token, estrategia)
    return bot
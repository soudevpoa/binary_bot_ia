import asyncio
import json
from core.bot_base import BotBase
from estrategias.reversao_tendencia import EstrategiaReversaoTendencia

# --- CLASSE DO BOT REAL ---
# Ela herda de BotBase, que cuida da lógica de inicialização, estatísticas, etc.
class BotReversao(BotBase):
    def __init__(self, config, token, estatisticas_file):
        # Instancia a sua estratégia de Reversão de Tendência.
        # Note que ela precisa do parâmetro "rsi_period" da sua configuração.
        estrategia = EstrategiaReversaoTendencia(config["rsi_period"])
        
        # Chama o construtor da classe-base (BotBase)
        # e passa a estratégia para ela.
        super().__init__(config, token, estrategia, estatisticas_file)
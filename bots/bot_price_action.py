import asyncio
import json
from core.bot_base import BotBase
from estrategias.price_action import EstrategiaPriceAction

# --- CLASSE DO BOT REAL ---
# Ela herda de BotBase, que cuida da lógica de inicialização, estatísticas, etc.
class BotPriceAction(BotBase):
    def __init__(self, config, token, estatisticas_file):
        # Instancia a sua estratégia de Price Action.
        # Note que a EstrategiaPriceAction() não precisa de argumentos de config,
        # então passamos vazia.
        estrategia = EstrategiaPriceAction()
        
        # Chama o construtor da classe-base (BotBase)
        # e passa a estratégia para ela.
        super().__init__(config, token, estrategia, estatisticas_file)
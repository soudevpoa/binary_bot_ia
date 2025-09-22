import asyncio
import json
from core.bot_base import BotBase
from estrategias.mm_rsi import EstrategiaMMRSI

# --- CLASSE DE ESTRATÉGIA (provavelmente já existe em estrategias/mm_rsi.py) ---
# Se sua EstrategiaMMRSI já existe e está importada, você não precisa disso.
# Apenas a lógica do BotMMRSI é necessária.
# Mas para o exemplo, vamos imaginar que a Estratégia é simples.
# class EstrategiaMMRSI:
#     def __init__(self, mm_curto, mm_longo, rsi_period, rsi_upper, rsi_lower):
#         self.mm_curto = mm_curto
#         # ... (e o restante da lógica) ...
#
#     def decidir(self, prices, volatilidade, limiar_volatilidade):
#         # Sua lógica de decisão para o bot MM_RSI
#         return "CALL", "mm_rsi" if ... else "PUT", "mm_rsi" if ...

# --- CLASSE DO BOT REAL ---
# Ela herda de BotBase, que cuida da lógica de inicialização, estatísticas, etc.
class BotMMRSI(BotBase):
    def __init__(self, config, token, estatisticas_file):
        # Instancia a sua estratégia.
        estrategia = EstrategiaMMRSI(
            mm_curto=config["mm_periodo_curto"],
            mm_longo=config["mm_periodo_longo"],
            rsi_period=config["rsi_period"],
            rsi_upper=config["rsi_upper"],
            rsi_lower=config["rsi_lower"]
        )
        
        # Chama o construtor da classe-base (BotBase)
        # e passa a estratégia para ela.
        super().__init__(config, token, estrategia, estatisticas_file)
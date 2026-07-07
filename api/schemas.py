from pydantic import BaseModel
from typing import Optional

class BotStartSchema(BaseModel):
    token: str
    par_moeda: str          # Ex: "R_100"
    estrategia: str         # Ex: "media_movel", "rsi", "ia"
    gestao_banca: str       # Ex: "martingale_inteligente", "soros", "stake_fixa"
    stake_inicial: float    # Ex: 1.0
    meta_lucro: float       # Ex: 5.0
    limite_perda: float     # Ex: 10.0
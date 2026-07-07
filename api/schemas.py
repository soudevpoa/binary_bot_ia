from pydantic import BaseModel

class BotStartSchema(BaseModel):
    token: str
    account_id: str  # 💡 Adicione esta linha aqui! Ex: "CR123456" ou "VRTC12345"
    par_moeda: str
    estrategia: str
    gestao_banca: str
    stake_inicial: float
    meta_lucro: float
    limite_perda: float
import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from core.executor import ExecutorBot  # Ajusta o import conforme o teu executor

app = FastAPI(title="Binary Bot Híbrido - API")

# Instância global do executor do bot
executor = None

class BotConfig(BaseModel):
    token: str
    estrategia: str
    stake: float
    stop_loss: float
    take_profit: float

@app.on_event("startup")
async def startup_event():
    global executor
    executor = ExecutorBot()

@app.post("/bot/start")
async def start_bot(config: BotConfig):
    global executor
    if executor.is_running:
        raise HTTPException(status_code=400, detail="O bot já está em execução.")
    
    # Inicia o loop do bot em background de forma totalmente assíncrona
    asyncio.create_task(executor.iniciar(config.dict()))
    return {"status": "sucesso", "mensagem": f"Bot iniciado com a estratégia {config.estrategia}"}

@app.post("/bot/stop")
async def stop_bot():
    global executor
    if not executor.is_running:
        raise HTTPException(status_code=400, detail="O bot já está parado.")
    
    await executor.parar()
    return {"status": "sucesso", "mensagem": "Comando de paragem enviado com sucesso."}

@app.get("/bot/status")
async def get_status():
    global executor
    return {
        "executando": executor.is_running,
        "saldo_atual": executor.saldo_atual if executor else 0,
        "lucro_total": executor.lucro_total if executor else 0
    }
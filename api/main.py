import sys
import os
import asyncio
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

# Garante que o Python encontre todas as pastas locais de módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.schemas import BotStartSchema

# Importação dinâmica dos bots configurados
from bots.bot_mm import BotMM
from bots.bot_rsi import BotRSI
from bots.bot_ia import BotIA
from bots.bot_price_action import BotPriceAction
from bots.bot_reversao import BotReversao

app = FastAPI(
    title="Binary Bot IA - API Gateway",
    description="Microsserviço de controle e gerenciamento dos robôs de trading",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rastreia as instâncias ativas dos bots e tarefas por usuário
ROBOS_ATIVOS = {}
TAREFAS_BACKGROUND = {}

def obter_instancia_bot(configuracao: BotStartSchema):
    """Fábrica dinâmica que mapeia as propriedades recebidas do Front para o formato esperado por cada bot"""
    estrategia = configuracao.estrategia.lower()
    
    # 💡 Montamos o dicionário unificado que o bot_ia.py e os arquivos de config .json originais usam
    config_dict = {
        "volatility_index": configuracao.par_moeda, # Ex: "R_100"
        "stake": configuracao.stake_inicial,
        "meta_lucro_percentual": 0.10,             # Valores padrão locais, customizáveis pelo front
        "stop_loss_percentual": 0.05,
        "mm_periodo_curto": 10,
        "mm_periodo_longo": 20,
        "modo_simulacao": False,
        "max_operacoes": 20
    }
    
    arquivo_estatisticas = "desempenho_ia.json"
    
    if estrategia == "media_movel":
        # Se os outros robôs esperam (par_moeda, token), mantemos o padrão funcional deles
        return BotMM(configuracao.par_moeda, configuracao.token)
    elif estrategia == "rsi":
        return BotRSI(configuracao.par_moeda, configuracao.token)
    elif estrategia == "ia":
        # 💡 CORREÇÃO DEFINITIVA: Garante que o arquivo nasça com chaves '{}' válidas para o json.load() não quebrar
        if not os.path.exists(arquivo_estatisticas) or os.path.getsize(arquivo_estatisticas) == 0:
            with open(arquivo_estatisticas, "w") as f:
                f.write("{}")
            print(f"📁 [API] Arquivo '{arquivo_estatisticas}' inicializado com JSON válido.")

        config_ia_padrao = {
            "volatility_index": configuracao.par_moeda,
            "stake": configuracao.stake_inicial,
            "meta_lucro_percentual": 0.10,
            "stop_loss_percentual": 0.05,
            "mm_periodo_curto": 10,
            "mm_periodo_longo": 20,
            "modo_simulacao": False,
            "max_operacoes": 20
        }
        
        return BotIA(config_ia_padrao, configuracao.token, arquivo_estatisticas)
        
        return BotIA(config_ia_padrao, configuracao.token, arquivo_estatisticas)
    elif estrategia == "price_action":
        return BotPriceAction(configuracao.par_moeda, configuracao.token)
    elif estrategia == "reversao":
        return BotReversao(configuracao.par_moeda, configuracao.token)
    else:
        raise ValueError(f"Estratégia '{configuracao.estrategia}' não reconhecida no sistema.")

async def gerenciar_ciclo_vida_bot(user_id: str, configuracao: BotStartSchema):
    """Inicializa a conexão websocket e executa a rotina do bot assincronamente"""
    bot = None
    try:
        bot = obter_instancia_bot(configuracao)
        ROBOS_ATIVOS[user_id] = bot
        
        print(f"🤖 [API] Inicializando {configuracao.estrategia.upper()} para {user_id} no ativo {configuracao.par_moeda}")
        
        # Executa o loop assíncrono principal (que conecta via WS, consome velas e usa o Executor)
        await bot.iniciar()
        
    except asyncio.CancelledError:
        print(f"🛑 [API] Tarefa do bot para {user_id} foi explicitamente cancelada.")
    except Exception as e:
        print(f"❌ [API] Erro crítico na execução do bot de {user_id}: {e}")
    finally:
        # Garante o fechamento seguro da conexão se ela ainda existir
        if bot and hasattr(bot, 'desconectar'):
            await bot.desconectar()
        ROBOS_ATIVOS.pop(user_id, None)
        TAREFAS_BACKGROUND.pop(user_id, None)
        print(f"🔌 [API] Robô de {user_id} totalmente finalizado e desconectado.")

@app.get("/")
def read_root():
    return {"status": "Online", "mensagem": "API do Binary Bot IA rodando perfeitamente!"}

@app.post("/api/v1/bot/iniciar")
async def iniciar_bot(payload: BotStartSchema, background_tasks: BackgroundTasks):
    user_id = "user_default_123"  # No futuro, resolvido via cabeçalho JWT
    
    if user_id in ROBOS_ATIVOS:
        raise HTTPException(status_code=400, detail="Este robô já está em execução para a sua conta!")
    
    try:
        # Validação preventiva de existência da estratégia
        obter_instancia_bot(payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # 💡 Correção: Mudamos a rota para 'async def' e passamos a tarefa direto para o background_tasks do FastAPI.
    # Isso faz o robô rodar no loop assíncrono principal e correto do servidor!
    background_tasks.add_task(gerenciar_ciclo_vida_bot, user_id, payload)
    
    # Criamos uma marcação temporária para o painel saber que a tarefa foi agendada
    ROBOS_ATIVOS[user_id] = "inicializando"
    
    return {
        "sucesso": True,
        "mensagem": f"Robô da estratégia '{payload.estrategia}' disparado com sucesso!",
        "ativo": payload.par_moeda
    }

@app.post("/api/v1/bot/parar")
async def parar_bot():
    user_id = "user_default_123"
    
    bot = ROBOS_ATIVOS.get(user_id)
    
    if not bot:
        return {"sucesso": False, "mensagem": "Nenhum robô ativo encontrado para interrupção."}
    
    print(f"⏹️ [API] Solicitando parada forçada para o robô de {user_id}...")
    
    # Como as classes originais herdam de BotBase e rodam um loop interno, 
    # se o seu bot tiver uma propriedade de controle (ex: self.conectado = False), nós alteramos ela aqui.
    # Se o método desconectar existir, nós forçamos a chamada dele:
    if bot != "inicializando" and hasattr(bot, 'desconectar'):
        try:
            # Criamos uma tarefa para desconectar de forma assíncrona segura
            asyncio.create_task(bot.desconectar())
        except Exception as e:
            print(f"⚠️ Erro ao forçar desconexão: {e}")
            
    ROBOS_ATIVOS.pop(user_id, None)
    return {"sucesso": True, "mensagem": "Ordem de parada enviada. Desconexão efetuada de forma limpa."}
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
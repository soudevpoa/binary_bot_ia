import os
import json
import asyncio
from config_loader import carregar_config
from core.bot_base import BotBase
from bots.bot_mm_rsi import iniciar_bot_mm_rsi
from bots.bot_rsi import iniciar_bot_rsi
from bots.bot_price_action import iniciar_bot_price_action
from bots.bot_reversao import iniciar_bot_reversao
from bots.bot_mm import iniciar_bot_mm
from bots.bot_ia import BotIA # Importação do Bot de IA

# Mapeia nome da estratégia para função de inicialização
estrategias_disponiveis = {
    "mm_rsi": iniciar_bot_mm_rsi,
    "rsi_bollinger": iniciar_bot_rsi,
    "price_action": iniciar_bot_price_action,
    "reversao_tendencia": iniciar_bot_reversao,
    "mm": iniciar_bot_mm,
    "ia": BotIA,  # Mapeia diretamente a classe, não a função de inicialização
}

def listar_configs():
    arquivos = os.listdir("configs")
    return [f for f in arquivos if f.startswith("config_") and f.endswith(".json")]

def extrair_nome_estrategia(nome_arquivo):
    return nome_arquivo.replace("config_", "").replace(".json", "")

def main():
    print("📂 Configurações disponíveis:")
    arquivos = listar_a=os.listdir("configs")
    arquivos_validos = [f for f in arquivos if extrair_nome_estrategia(f) in estrategias_disponiveis]
    
    if not arquivos_validos:
        print("❌ Nenhuma configuração válida encontrada.")
        print("Certifique-se de que os arquivos 'config_*.json' correspondem a uma estratégia mapeada.")
        return

    for i, nome in enumerate(arquivos_validos):
        print(f"{i + 1}. {nome}")

    escolha = input("\nDigite o número da estratégia que deseja iniciar: ")
    try:
        indice = int(escolha) - 1
        nome_arquivo = arquivos_validos[indice]
    except (ValueError, IndexError):
        print("❌ Escolha inválida.")
        return

    nome_estrategia = extrair_nome_estrategia(nome_arquivo)
    config_path = os.path.join("configs", nome_arquivo)
    config = carregar_config(config_path)
    token = config["token"]
    
    # Define o nome do arquivo de estatísticas com base na estratégia
    estatisticas_file = f"estatisticas_{nome_estrategia}.json"

    print(f"\n🚀 Iniciando bot com estratégia: {nome_estrategia}")
    
    # Obtém a classe ou função de inicialização do dicionário
    iniciador_bot = estrategias_disponiveis.get(nome_estrategia)
    
    if iniciador_bot:
        if isinstance(iniciador_bot, type): # Se for uma classe (como BotIA)
            bot = iniciador_bot(config, token, estatisticas_file)
        else: # Se for uma função (como iniciar_bot_rsi)
            bot = iniciador_bot(config, token, estatisticas_file)
            
        asyncio.run(bot.iniciar())
    else:
        print(f"❌ Estratégia '{nome_estrategia}' não está mapeada no dicionário.")

if __name__ == "__main__":
    main()
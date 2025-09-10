import os
import json
from config_loader import carregar_config
from bots.bot_mm_rsi import iniciar_bot_mm_rsi
from bots.bot_rsi import iniciar_bot_rsi
from bots.bot_price_action import iniciar_bot_price_action
from bots.bot_reversao import iniciar_bot_reversao
from bots.bot_mm import iniciar_bot_mm


import asyncio

# Mapeia nome da estratégia para função de inicialização
estrategias_disponiveis = {
    "mm_rsi": iniciar_bot_mm_rsi,
    "rsi_bollinger": iniciar_bot_rsi,
    "price_action": iniciar_bot_price_action,
    "reversao_tendencia": iniciar_bot_reversao,
    "mm": iniciar_bot_mm,
  
    
}


def listar_configs():
    arquivos = os.listdir("configs")
    return [f for f in arquivos if f.startswith("config_") and f.endswith(".json")]

def extrair_nome_estrategia(nome_arquivo):
    return nome_arquivo.replace("config_", "").replace(".json", "")

def main():
    print("📂 Configurações disponíveis:")
    arquivos = listar_configs()
    for i, nome in enumerate(arquivos):
        print(f"{i + 1}. {nome}")

    escolha = input("\nDigite o número da estratégia que deseja iniciar: ")
    try:
        indice = int(escolha) - 1
        nome_arquivo = arquivos[indice]
    except (ValueError, IndexError):
        print("❌ Escolha inválida.")
        return

    nome_estrategia = extrair_nome_estrategia(nome_arquivo)
    config_path = os.path.join("configs", nome_arquivo)
    config = carregar_config(config_path)
    token = config["token"]

    if nome_estrategia not in estrategias_disponiveis:
        print(f"❌ Estratégia '{nome_estrategia}' não está mapeada.")
        return

    print(f"\n🚀 Iniciando bot com estratégia: {nome_estrategia}")
    bot = estrategias_disponiveis[nome_estrategia](config, token)
    asyncio.run(bot.iniciar())

if __name__ == "__main__":
    main()
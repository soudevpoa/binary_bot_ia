import asyncio
import json
import os
from bots.bot_megalodon import BotMegalodon
from bots.bot_mm_rsi import BotMMRSI
from bots.bot_mm import BotMM
from bots.bot_price_action import BotPriceAction
from bots.bot_reversao import BotReversao
from bots.bot_rsi import BotRSI

# Define uma lista de bots disponíveis.
# Adicione novos bots aqui quando eles estiverem prontos.
BOTS_DISPONIVEIS = {
    "1": {"nome": "megalodon", "class": BotMegalodon},
    "2": {"nome": "mm_rsi", "class": BotMMRSI},
    "3": {"nome": "mm", "class": BotMM},
    "4": {"nome": "price_action", "class": BotPriceAction},
    "5": {"nome": "reversao", "class": BotReversao},
    "6": {"nome": "rsi", "class": BotRSI},

}

async def main():
    print("Iniciando bot...")

    # Carrega o arquivo de configuração.
    with open("configs/config_megalodon.json", "r") as f:
        config = json.load(f)
    
    token = config.get("token")
    if not token:
        print("Erro: O token não foi encontrado no arquivo de configuração.")
        return
        
    # 🚨 NOVO CÓDIGO DO MENU DE SELEÇÃO
    while True:
        print("\n--- Selecione o bot para iniciar ---")
        for numero, bot_info in BOTS_DISPONIVEIS.items():
            print(f"[{numero}] {bot_info['nome'].capitalize()}")
        
        escolha = input("Digite o número do bot desejado: ")
        
        if escolha in BOTS_DISPONIVEIS:
            bot_selecionado = BOTS_DISPONIVEIS[escolha]["nome"]
            BotClass = BOTS_DISPONIVEIS[escolha]["class"]
            break
        else:
            print("❌ Opção inválida. Por favor, digite o número correto.")

    print(f"✅ Bot '{bot_selecionado.capitalize()}' selecionado.")
    
    # --- O RESTO DO CÓDIGO QUE JÁ AJUSTAMOS PERMANECE IGUAL ---
    
    # Cria a pasta de estatísticas se não existir.
    pasta_estatisticas = "estatisticas"
    if not os.path.exists(pasta_estatisticas):
        os.makedirs(pasta_estatisticas)
        print(f"✅ Pasta '{pasta_estatisticas}' criada com sucesso.")

    # Constrói o caminho completo do arquivo de estatísticas
    estatisticas_file_path = os.path.join(pasta_estatisticas, f"{bot_selecionado}_analise.json")
    
    # Inicia o bot
    bot = BotClass(config, token, estatisticas_file_path)

    await bot.iniciar()

if __name__ == "__main__":
    asyncio.run(main())
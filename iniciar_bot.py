import asyncio
import json
import os
from dotenv import load_dotenv

# Imports das estratégias
from bots.bot_mm_rsi import BotMMRSI
from bots.bot_mm import BotMM
from bots.bot_price_action import BotPriceAction
from bots.bot_reversao import BotReversao
from bots.bot_rsi import BotRSI

class ConfigWrapper:
    def __init__(self, dados_dict):
        self.json = dados_dict  # Atende o core (ex: config.json)
        self._dados = dados_dict

    # Atende as estratégias específicas (ex: config["mm_periodo_curto"])
    def __getitem__(self, item):
        return self._dados[item]
    
    # Caso alguma estratégia tente usar o método .get() igual dicionário
    def get(self, item, default=None):
        return self._dados.get(item, default)
# Menu atualizado sem a opção do Megalodon
BOTS_DISPONIVEIS = {
    "1": {"nome": "mm_rsi", "class": BotMMRSI},
    "2": {"nome": "mm", "class": BotMM},
    "3": {"nome": "price_action", "class": BotPriceAction},
    "4": {"nome": "reversao", "class": BotReversao},
    "5": {"nome": "rsi", "class": BotRSI},
}

async def main():
    print("Iniciando sistema de bots...")
    
    load_dotenv()
    # Captura, remove espaços e elimina aspas acidentais que possam ter vindo do arquivo .env
    token = os.getenv("DERIV_API_TOKEN", "").strip().replace('"', '').replace("'", "")

    if not token:
        raise ValueError("ERRO: O DERIV_API_TOKEN não foi encontrado no ficheiro .env!")

    print("\n--- Escolha a Estratégia Técnica ---")
    for chave, info in BOTS_DISPONIVEIS.items():
        print(f"[{chave}] - {info['nome'].upper()}")
        
    escolha = input("\nDigite o número da estratégia desejada: ").strip()
    
    if escolha not in BOTS_DISPONIVEIS:
        print("Opção inválida!")
        return

    estrategia_selecionada = BOTS_DISPONIVEIS[escolha]
    
    # Ajuste fino automático para bater com os nomes exatos dos arquivos na pasta configs/
    if estrategia_selecionada['nome'] == "reversao":
        nome_config = "config_reversao_tendencia.json"
    elif estrategia_selecionada['nome'] == "rsi":
        nome_config = "config_rsi_bollinger.json"
    else:
        nome_config = f"config_{estrategia_selecionada['nome']}.json"

    caminho_config = os.path.join("configs", nome_config)

    if not os.path.exists(caminho_config):
        print(f"Erro: Arquivo de configuração {caminho_config} não encontrado!")
        return

    with open(caminho_config, "r", encoding="utf-8") as f:
        config_puro = json.load(f)

    # Transformamos o dicionário no objeto com a propriedade .json que o bot_base quer!
    config_adaptado = ConfigWrapper(config_puro)

    estatisticas_file = "desempenho.json"    
    
    print(f"\nLigando o Bot com a estratégia: {estrategia_selecionada['nome'].upper()}...")
    
    # Inicializa passando o config adaptado
    bot = estrategia_selecionada["class"](
        config=config_adaptado, 
        token=token, 
        estatisticas_file=estatisticas_file
    )
    
    # Inicia a execução assíncrona do bot
    await bot.iniciar()

if __name__ == "__main__":
    asyncio.run(main())
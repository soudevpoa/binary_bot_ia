# No arquivo treinar_modelo.py

import asyncio
import json
import numpy as np
import os
from core.modelo_neural import ModeloNeural
from indicadores.indicadores import calcular_rsi, calcular_mm, calcular_volatilidade
from core.mercado import Mercado

# Define o número de ticks que você quer usar para o treinamento.
# É uma boa prática deixar isso como uma variável para facilitar o ajuste.
NUMERO_TICKS_TREINO = 20000 

async def coletar_dados(token, ativo, num_ticks):
    """Função para coletar ticks do mercado."""
    mercado = Mercado("wss://ws.derivws.com/websockets/v3?app_id=1089", token, ativo)
    await mercado.conectar()
    await mercado.autenticar(token) # Adicionamos a autenticação para garantir
    await mercado.subscrever_ticks(ativo)

    prices = []
    print(f"📦 Coletando {num_ticks} ticks do {ativo}...")
    for _ in range(num_ticks):
        try:
            msg = await mercado.ws.recv()
            data = mercado.processar_tick(msg)
            if data and data['msg_type'] == 'tick':
                prices.append(data["price"])
                # print(f"📥 Tick recebido: {data['price']}") # Descomente para ver o log de ticks
        except Exception as e:
            print(f"⚠️ Erro ao coletar ticks: {e}")
            break
    
    await mercado.desconectar()
    return prices

def preparar_dataset(prices, config):
    """Prepara o dataset para o treinamento da IA."""
    features, labels = [], []
    # Usamos os parâmetros do config.json
    periodo_min = max(config.get("mm_periodo_longo", 20), 14)
    window_size = periodo_min

    for i in range(len(prices) - window_size - 1):
        subset = prices[i:i+window_size]
        next_price = prices[i+window_size]

        rsi = calcular_rsi(subset)
        mm_curta = calcular_mm(subset, config["mm_periodo_curto"])
        mm_longa = calcular_mm(subset, config["mm_periodo_longo"])
        vol = calcular_volatilidade(subset)

        f = np.array([rsi, mm_curta, mm_longa, vol])
        features.append(f)
        labels.append(1 if next_price > subset[-1] else 0)

    return np.array(features), np.array(labels)

async def main():
    """Função principal para o treinamento do modelo."""
    try:
        # 🚨 CORREÇÃO 1: Lê as configurações do arquivo
        with open("configs/config_megalodon.json", "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        print("❌ Erro: arquivo config_megalodon.json não encontrado.")
        return

    token = config.get("token")
    ativo = config.get("volatility_index")
    
    if not token or not ativo:
        print("❌ Erro: Token ou Volatility Index ausentes no config_megalodon.json.")
        return

    # 🚨 CORREÇÃO 2: Usa as variáveis do config.json
    prices = await coletar_dados(token, ativo, num_ticks=NUMERO_TICKS_TREINO)

    if not prices:
        print("❌ Não foi possível coletar dados de preço. Verifique sua conexão ou token.")
        return

    print("🧪 Preparando dataset...")
    X, y = preparar_dataset(prices, config)

    if len(X) == 0:
        print("❌ Dados insuficientes para treino. Tente aumentar o número de ticks.")
        return

    print(f"🧠 Treinando modelo com {len(X)} amostras...")
    modelo = ModeloNeural()
    modelo.treinar(X, y)

    # 🚨 CORREÇÃO 3: Usamos os métodos da classe para salvar os arquivos
    print("💾 Salvando modelo e scaler...")
    modelo.salvar_modelo("modelo_megalodon.h5")
    modelo.salvar_scaler("scaler_megalodon.pkl")

    print(f"✅ Treinamento concluído e arquivos salvos. Acurácia: {modelo.acuracia:.2f}%")

if __name__ == "__main__":
    asyncio.run(main())
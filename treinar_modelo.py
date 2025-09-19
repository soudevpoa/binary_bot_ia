import asyncio
import joblib
import numpy as np
from core.modelo_neural import ModeloNeural
from indicadores.indicadores import calcular_rsi, calcular_mm, calcular_volatilidade
from core.mercado import Mercado

async def coletar_dados(token, ativo, num_ticks=200):
    mercado = Mercado("wss://ws.derivws.com/websockets/v3?app_id=1089", token, ativo)
    await mercado.conectar()
    await mercado.subscrever_ticks(ativo)

    prices = []
    for _ in range(num_ticks):
        try:
            msg = await mercado.ws.recv()
            data = mercado.processar_tick(msg)
            if data:
                prices.append(data["price"])
                print(f"📥 Tick recebido: {data['price']}")
        except Exception as e:
            print(f"⚠️ Erro ao coletar ticks: {e}")
            break
    return prices

def preparar_dataset(prices, config):
    features, labels = [], []
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
    config = {
        "token": "GT5nKSpPMDLIJIg",
        "volatility_index": "R_100",
        "mm_periodo_curto": 5,
        "mm_periodo_longo": 20
    }

    print("📦 Coletando dados do mercado...")
    prices = await coletar_dados(config["token"], config["volatility_index"], num_ticks=600)


    print("🧪 Preparando dataset...")
    X, y = preparar_dataset(prices, config)

    if len(X) == 0:
        print("❌ Dados insuficientes para treino.")
        return

    print("🧠 Treinando modelo...")
    modelo = ModeloNeural()
    modelo.treinar(X, y)

    print("💾 Salvando modelo e scaler...")
    print("📐 Média do scaler:", modelo.scaler.mean_)
    modelo.salvar_modelo("modelo_megalodon.h5")
    joblib.dump(modelo.scaler, "scaler_megalodon.pkl")

    print("✅ Treinamento concluído e arquivos salvos.")

asyncio.run(main())

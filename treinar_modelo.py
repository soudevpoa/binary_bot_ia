import asyncio
import json
import numpy as np
import os
from core.modelo_neural import ModeloNeural
# Deixamos os imports abaixo caso você decida usar indicadores no futuro, mas não são usados agora.
from indicadores.indicadores import calcular_rsi, calcular_mm, calcular_volatilidade 
from core.mercado import Mercado
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler

# Define o número de ticks que você quer usar para o treinamento.
NUMERO_TICKS_TREINO = 50000 

async def coletar_dados(token, ativo, num_ticks):
    """Função para coletar ticks do mercado."""
    mercado = Mercado("wss://ws.derivws.com/websockets/v3?app_id=1089", token, ativo)
    await mercado.conectar()
    await mercado.autenticar(token)
    await mercado.subscrever_ticks(ativo)

    prices = []
    print(f"📦 Coletando {num_ticks} ticks do {ativo}...")
    for _ in range(num_ticks):
        try:
            msg = await mercado.ws.recv()
            data = mercado.processar_tick(msg)
            if data and data.get('msg_type') == 'tick':
                prices.append(data["price"])
        except Exception as e:
            print(f"⚠️ Erro ao coletar ticks: {e}")
            break
    
    await mercado.desconectar()
    print("🔌 Conexão com o Mercado Deriv fechada.")
    return prices

def preparar_dataset(prices, config):
    """
    ✅ AJUSTE: Prepara o dataset para o treinamento da IA, usando os últimos N preços brutos.
    """
    features, labels = [], []
    # Usa o tamanho da janela definido no config.json (200)
    window_size = config.get("tamanho_janela_ia", 200) 

    # O loop precisa de pelo menos o tamanho da janela + 1 para o label
    for i in range(len(prices) - window_size - 1):
        # X: O conjunto de 200 preços anteriores (features)
        X_subset = prices[i:i + window_size] 
        
        # y: O próximo preço (para definir o label)
        next_price = prices[i + window_size] 

        # A feature é a lista dos 200 preços.
        features.append(X_subset) 
        
        # O Label é 1 para CALL (subida) e 0 para PUT (descida/lateralização)
        labels.append(1 if next_price > X_subset[-1] else 0)

    return np.array(features), np.array(labels)

async def main():
    """Função principal para o treinamento do modelo."""
    try:
        if not os.path.exists("configs/config_megalodon.json"):
            raise FileNotFoundError("config_megalodon.json não encontrado. Verifique o caminho.")
        with open("configs/config_megalodon.json", "r") as f:
            config = json.load(f)
    except FileNotFoundError as e:
        print(f"❌ Erro: {e}")
        return

    token = config.get("token")
    ativo = config.get("volatility_index")
    window_size = config.get("tamanho_janela_ia", 200)
    
    if not token or not ativo:
        print("❌ Erro: Token ou Volatility Index ausentes no config_megalodon.json.")
        return

    prices = await coletar_dados(token, ativo, num_ticks=NUMERO_TICKS_TREINO)

    if not prices:
        print("❌ Não foi possível coletar dados de preço. Verifique sua conexão ou token.")
        return

    print("🧪 Preparando dataset...")
    X, y = preparar_dataset(prices, config)

    if len(X) == 0:
        print("❌ Dados insuficientes para treino. Tente aumentar o número de ticks ou a janela IA.")
        return
    
    print(f"🧠 Treinando modelo com {len(X)} amostras e {window_size} features...")
    # ✅ AJUSTE: Inicializa o modelo com o input_shape correto (200)
    modelo = ModeloNeural(input_shape=window_size) 
    
    # ----------------------------------------------------
    # ✅ AJUSTE CRÍTICO: Normalizar os dados e fitar o Scaler
    # ----------------------------------------------------
    print("⚖️ Normalizando e preparando dados...")
    scaler = MinMaxScaler()
    # O scaler é treinado (fitado) com o conjunto COMPLETO de features X (N, 200)
    X_normalizado = scaler.fit_transform(X) 
    
    # Associa o scaler ao modelo para que ele possa ser salvo e usado na operação
    modelo.scaler = scaler
    
    # Divide os dados normalizados
    X_treino, X_teste, y_treino, y_teste = train_test_split(
        X_normalizado, y, test_size=0.2, random_state=42
    )
    
    print(f"🧠 Treinando modelo com {len(X_treino)} amostras de treino...")
    # ----------------------------------------------------
    # ✅ FIM DO AJUSTE
    # ----------------------------------------------------
    
    modelo.treinar(X_treino, y_treino, X_teste, y_teste)

    # Usamos os métodos da classe para salvar os arquivos
    print("💾 Salvando modelo e scaler...")
    modelo.salvar("modelo_megalodon.h5")
    modelo.salvar_scaler("scaler_megalodon.pkl")

    # A acurácia deve ser acessada via atributo do modelo após o treino (se implementado)
    print(f"✅ Treinamento concluído e arquivos salvos.") 

if __name__ == "__main__":
    asyncio.run(main())
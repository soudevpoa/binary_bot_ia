import streamlit as st
import joblib
import numpy as np
from keras.models import load_model

st.set_page_config(page_title="Painel Megalodon", layout="wide")

st.title("🦈 Painel de IA - Megalodon")

# 🔁 Carregar modelo e scaler
try:
    model = load_model("modelo_megalodon.h5")
    scaler = joblib.load("scaler_megalodon.pkl")
    st.success("✅ Modelo e scaler carregados com sucesso.")
except Exception as e:
    st.error(f"❌ Erro ao carregar IA: {e}")
    st.stop()

# 📊 Simular entrada de dados
st.subheader("📥 Simulação de entrada")
rsi = st.slider("RSI", 0.0, 100.0, 50.0)
mm_curta = st.number_input("Média Móvel Curta", value=1130.0)
mm_longa = st.number_input("Média Móvel Longa", value=1131.0)
volatilidade = st.slider("Volatilidade", 0.0, 1.0, 0.5)

features = np.array([[rsi, mm_curta, mm_longa, volatilidade]])
features_scaled = scaler.transform(features)
prob = model.predict(features_scaled, verbose=0)[0][0]

# 🎯 Resultado da previsão
st.subheader("🎯 Previsão da IA")
if prob > 0.5:
    st.metric("Direção prevista", "CALL", delta=f"{prob:.2%}")
else:
    st.metric("Direção prevista", "PUT", delta=f"{(1 - prob):.2%}")

# 📈 Histórico e desempenho (placeholder)
st.subheader("📈 Desempenho histórico")
st.line_chart([prob, 1 - prob])  # Exemplo simples


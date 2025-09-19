import streamlit as st
import requests
import os
import json
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# 🧭 Configuração da página
st.set_page_config(page_title="Painel Megalodon", layout="wide")
st_autorefresh(interval=5000, limit=None, key="painel_refresh")
st.title("🦈 Painel de Comando - Megalodon")

# 🧠 Controle do Bot via API
st.subheader("🧠 Controle do Bot Megalodon")
col1, col2 = st.columns(2)

with col1:
    if st.button("▶️ Iniciar Bot"):
        try:
            r = requests.post("http://localhost:5000/iniciar")
            st.success(r.json()["status"])
        except Exception as e:
            st.error(f"Erro ao iniciar bot: {e}")

with col2:
    if st.button("⏹️ Parar Bot"):
        try:
            r = requests.post("http://localhost:5000/parar")
            st.warning(r.json()["status"])
        except Exception as e:
            st.error(f"Erro ao parar bot: {e}")

# 📡 Consulta de status
st.subheader("📡 Status do Bot")
status = None  # Inicializa a variável

try:
    status = requests.get("http://localhost:5000/status").json()
    st.metric("Loss Virtual", f"{status['loss_virtual_count']}/{status['limite_loss_virtual']}")
    st.metric("Stake Base", f"{status['stake_base']}")
    st.metric("Bot Ativo", "✅" if status["ativo"] else "⛔️")
except Exception as e:
    st.error(f"Erro ao consultar status: {e}")

# ⚙️ Atualização de parâmetros
st.subheader("⚙️ Atualizar Configurações")

if status:
    novo_stake = st.number_input("Novo Stake Base", value=status["stake_base"])
    novo_limite = st.slider("Novo Limite de Loss Virtual", 1, 10, value=status["limite_loss_virtual"])

    if st.button("Salvar na API"):
        try:
            r = requests.post("http://localhost:5000/atualizar_config", json={
                "stake_base": novo_stake,
                "limite_loss_virtual": novo_limite
            })
            st.success(r.json()["status"])
        except Exception as e:
            st.error(f"Erro ao salvar configurações: {e}")
else:
    st.warning("⚠️ API não respondeu — configurações não disponíveis.")

# 📜 Histórico de Operações
st.subheader("📜 Histórico de Operações")

operacoes_path = "painel/operacoes.json"
if os.path.exists(operacoes_path):
    try:
        with open(operacoes_path) as f:
            operacoes = json.load(f)
        if operacoes:
            df = pd.DataFrame(operacoes)
            st.dataframe(df)
            if "saldo" in df.columns:
                st.line_chart(df["saldo"])
        else:
            st.info("ℹ️ Nenhuma operação registrada ainda.")
    except Exception as e:
        st.error(f"Erro ao carregar histórico: {e}")
else:
    st.warning("⚠️ Arquivo de operações não encontrado.")

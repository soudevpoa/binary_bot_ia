import streamlit as st
import json
import time

st.set_page_config(page_title="Painel do Bot", layout="wide")
st.title("📊 Painel de Operações em Tempo Real")

placeholder = st.empty()

while True:
    try:
        with open("dados/painel_status.json") as f:
            dados = json.load(f)
    except:
        dados = {}

    with placeholder.container():
        st.metric("⏱️ Última atualização", dados.get("timestamp", "--"))
        st.metric("💰 Lucro acumulado", f"{dados.get('lucro', 0):.2f}")
        st.metric("📉 Volatilidade", f"{dados.get('volatilidade', 0):.5f}")
        st.metric("📐 Limiar", f"{dados.get('limiar', 0):.5f}")
        st.metric("📶 Sinal", dados.get("sinal", "Nenhum"))
        st.metric("📊 Padrão", dados.get("padrao", "--"))
        st.metric("💹 Preço atual", f"{dados.get('preco', 0):.5f}")

    time.sleep(2)
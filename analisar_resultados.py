import json
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

def carregar_historico(caminho):
    with open(caminho, "r") as f:
        linhas = f.readlines()
    registros = [json.loads(linha) for linha in linhas]
    return pd.DataFrame(registros)

def analisar(df):
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["hora"] = df["timestamp"].dt.hour
    df["acerto"] = df["resultado"].apply(lambda x: 1 if x == "win" else 0)

    taxa_acerto = df["acerto"].mean() * 100
    print(f"✅ Taxa de acerto geral: {taxa_acerto:.2f}%")

    acertos_por_hora = df.groupby("hora")["acerto"].mean() * 100
    acertos_por_direcao = df.groupby("direcao")["acerto"].mean() * 100

    plt.figure(figsize=(12, 5))
    plt.subplot(1, 2, 1)
    acertos_por_hora.plot(kind="bar", color="skyblue")
    plt.title("Taxa de acerto por hora")
    plt.xlabel("Hora do dia")
    plt.ylabel("Acerto (%)")

    plt.subplot(1, 2, 2)
    acertos_por_direcao.plot(kind="bar", color="salmon")
    plt.title("Acerto por tipo de entrada")
    plt.xlabel("Direção")
    plt.ylabel("Acerto (%)")

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    df = carregar_historico("historico_megalodon.json")
    analisar(df)

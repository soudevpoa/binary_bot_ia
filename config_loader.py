import json

def carregar_config(caminho):
    with open(caminho, "r") as f:
        return json.load(f)

import json

def carregar_config(caminho="config.json"):
    with open(caminho, "r") as f:
        return json.load(f)
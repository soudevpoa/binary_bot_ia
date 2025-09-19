from flask import Flask, request, jsonify
import threading
import asyncio
from bots.bot_megalodon import BotMegalodon
from core.mercado import Mercado
import os

app = Flask(__name__)

# Estado do bot
estado_bot = {
    "ativo": False,
    "loss_virtual_count": 0,
    "stake_base": 2.0,
    "limite_loss_virtual": 4
}

bot_thread = None

def executar_bot():
    config = {
        "stake_base": estado_bot["stake_base"],
        "limite_loss_virtual": estado_bot["limite_loss_virtual"],
        "modo_simulacao": False,
        "mm_periodo_curto": 5,
        "mm_periodo_longo": 20,
        "limiar_volatilidade": 0.2
    }

    token = "SEU_TOKEN_AQUI"
    url = "wss://ws.binaryws.com/websockets/v3?app_id=1089"  # ✅ URL da corretora
    os.makedirs("painel", exist_ok=True)
    estatisticas_file = os.path.join("painel", "estatisticas.json")

    bot = BotMegalodon(config, token, estatisticas_file)
    bot.mercado = Mercado(url, token, config["limiar_volatilidade"])  # ✅ Corrigido
    asyncio.run(bot.iniciar())


@app.route("/iniciar", methods=["POST"])
def iniciar():
    global bot_thread
    if bot_thread is None or not bot_thread.is_alive():
        bot_thread = threading.Thread(target=executar_bot)
        bot_thread.start()
        estado_bot["ativo"] = True
        return jsonify({"status": "Bot iniciado com sucesso."})
    else:
        return jsonify({"status": "Bot já está em execução."})

@app.route("/parar", methods=["POST"])
def parar():
    estado_bot["ativo"] = False
    return jsonify({"status": "Sinal enviado para parar o bot."})

@app.route("/status", methods=["GET"])
def status():
    return jsonify(estado_bot)

@app.route("/atualizar_config", methods=["POST"])
def atualizar_config():
    data = request.json
    estado_bot.update(data)
    return jsonify({"status": "Configurações atualizadas", "config": estado_bot})

def rodar_api():
    app.run(port=5000)

if __name__ == "__main__":
    rodar_api()

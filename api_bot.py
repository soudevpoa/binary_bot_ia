from flask import Flask, request, jsonify
import threading

app = Flask(__name__)

# Estado do bot (simulado)
estado_bot = {
    "ativo": False,
    "loss_virtual_count": 0,
    "stake_base": 2.0,
    "limite_loss_virtual": 4
}

@app.route("/iniciar", methods=["POST"])
def iniciar():
    estado_bot["ativo"] = True
    return jsonify({"status": "Bot iniciado"})

@app.route("/parar", methods=["POST"])
def parar():
    estado_bot["ativo"] = False
    return jsonify({"status": "Bot parado"})

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

# Roda em thread separada se quiser embutir no bot
if __name__ == "__main__":
    rodar_api()

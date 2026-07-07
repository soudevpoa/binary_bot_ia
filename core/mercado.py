import json
import websockets
import asyncio
import os
import requests
from collections import deque

class Mercado:
    def __init__(self, url, token, volatility_index):
        app_id = os.getenv("APP_ID", "").strip() or "36544"
        base_url = url.split("?")[0]
        self.url = f"{base_url}?app_id={app_id}"

        self.token = str(token).strip().replace('"', '').replace("'", "")
        self.volatility_index = volatility_index
        self.precos = deque(maxlen=200)
        self.ws = None

        # Handlers e fila de mensagens
        self.handlers = []
        self.queue = asyncio.Queue()

    def registrar_handler(self, handler):
        """Permite que outros módulos registrem callbacks para mensagens"""
        self.handlers.append(handler)

    async def conectar(self, account_id=None):
        ws_url = self.gerar_otp(account_id)
        print("🔌 Conectando ao servidor da Deriv com OTP...")
        # ✅ ping_interval e ping_timeout para evitar queda por keepalive
        self.ws = await websockets.connect(ws_url, ping_interval=20, ping_timeout=20)

    def gerar_otp(self, account_id):
        url = f"https://api.derivws.com/trading/v1/options/accounts/{account_id}/otp"
        app_id = os.getenv("APP_ID", "1089").strip()
        headers = {
            "Deriv-App-Id": app_id,
            "Authorization": f"Bearer {self.token}"
        }
        response = requests.post(url, headers=headers)
        otp_data = response.json()
        if response.status_code == 200 and "data" in otp_data and "url" in otp_data["data"]:
            return otp_data["data"]["url"]
        else:
            raise Exception(f"Erro ao gerar OTP: {otp_data}")

    async def autenticar(self, token):
        await self.ws.send(json.dumps({"authorize": self.token}))
        response = await self.ws.recv()
        data = json.loads(response)
        if data.get("msg_type") == "authorize" and "error" not in data:
            print("🔐 Autenticado com sucesso na Deriv usando PAT!")
            return True

    async def subscrever_ticks(self, symbol):
        await self.ws.send(json.dumps({"ticks": symbol, "subscribe": 1}))
        print(f"📈 Subscrição iniciada para {symbol}")

    async def carregar_ticks_iniciais(self, symbol, count=100):
        """Carrega ticks históricos antes de iniciar o loop de manutenção"""
        request = {
            "ticks_history": symbol,
            "count": count,
            "end": "latest",
            "style": "ticks"
        }
        await self.ws.send(json.dumps(request))
        response = await self.ws.recv()
        data = json.loads(response)

        precos = []
        if "history" in data and "prices" in data["history"]:
            precos = [float(p) for p in data["history"]["prices"]]
        return precos

    async def manter_conexao(self, account_id):
        while True:
            try:
                msg = await self.ws.recv()   # ✅ único recv central
                data = json.loads(msg)

                # Envia para fila
                await self.queue.put(data)

                # Distribui para handlers registrados
                for handler in self.handlers:
                    await handler(data)

            except Exception as e:
                print(f"⚠️ Erro no loop de mensagens: {e}")
                try:
                    await self.conectar(account_id=account_id)
                    await self.autenticar(self.token)
                    await self.subscrever_ticks(self.volatility_index)
                    print("🔄 Reconectado após falha.")
                except Exception as reconectar_erro:
                    print(f"❌ Falha ao reconectar: {reconectar_erro}")
                await asyncio.sleep(5)

    def processar_tick(self, data):
        if 'tick' in data and 'symbol' in data['tick']:
            tick_data = data['tick']
            preco = float(tick_data['quote'])
            self.precos.append(preco)
            return {
                'price': preco,
                'msg_type': data.get('msg_type'),
                'symbol': tick_data.get('symbol'),
                'epoch': tick_data.get('epoch')
            }
        return None

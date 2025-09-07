import json
import websockets
import ssl
import asyncio

class Mercado:
    def __init__(self, url, token, volatility_index):
        self.url = url
        self.token = token
        self.volatility_index = volatility_index


    async def conectar(self):
        self.ws = await websockets.connect(self.url)

    async def autenticar(self, token):
        await self.ws.send(json.dumps({"authorize": token}))
        response = await self.ws.recv()
        data = json.loads(response)
        if "authorize" in data:
            print("🔐 Autenticado com sucesso!")
            return True
        print(f"❌ Falha na autenticação: {data}")
        return False

    async def subscrever_ticks(self, symbol):
        await self.ws.send(json.dumps({"ticks": symbol}))
        print(f"📈 Subscrição iniciada para {symbol}")

    async def manter_conexao(self):
     while True:
        try:
            await self.ws.send(json.dumps({"ping": 1}))
            await asyncio.sleep(30)
        except Exception as e:
            print(f"⚠️ Erro no ping: {e}")
            try:
                await self.conectar()
                await self.autenticar(self.token)
                await self.subscrever_ticks(self.volatility_index)
                print("🔄 Reconectado após falha no ping.")
            except Exception as reconectar_erro:
                print(f"❌ Falha ao reconectar: {reconectar_erro}")
            await asyncio.sleep(5)
            continue

    def processar_tick(self, msg):
        data = json.loads(msg)
        if "tick" in data:
            return {"price": float(data["tick"]["quote"])}
        return None
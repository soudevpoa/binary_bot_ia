import json
import websockets
import asyncio
import os
from collections import deque

class Mercado:
    def __init__(self, url, token, volatility_index):
        # Lê o APP_ID real do seu arquivo .env e limpa espaços
        app_id = os.getenv("APP_ID", "").strip()
        
        # Fallback de segurança caso o .env esteja vazio por algum motivo
        if not app_id:
            print("⚠️ AVISO: APP_ID não encontrado no .env! Usando padrão universal.")
            app_id = "36544"
        
        # Limpa e reconstrói a URL usando o ID correto
        base_url = url.split("?")[0]
        self.url = f"{base_url}?app_id={app_id}"
            
        self.token = str(token).strip().replace('"', '').replace("'", "")
        self.volatility_index = volatility_index
        self.precos = deque(maxlen=200)
        self.ws = None

    async def conectar(self):
        # Mudamos o print para mostrar o app_id real que definimos no __init__ (o "36544")
        print(f"🔌 Conectando ao servidor da Deriv (App ID: {self.url.split('app_id=')[1]})...")
        self.ws = await websockets.connect(self.url)

    async def autenticar(self, token):
        # Usamos o token que já foi limpo no __init__
        await self.ws.send(json.dumps({"authorize": self.token}))
        
        response = await self.ws.recv()
        data = json.loads(response)
        
        if data.get("msg_type") == "authorize" and "error" not in data:
            print("🔐 Autenticado com sucesso na Deriv!")
            return True
            
        print(f"❌ Falha na autenticação: {data}")
        return False

    async def subscrever_ticks(self, symbol):
        await self.ws.send(json.dumps({"ticks": symbol, "subscribe": 1}))
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

    def get_precos(self):
        return list(self.precos)
        
    async def desconectar(self):
        if self.ws:
            await self.ws.close()
            print("🔌 Conexão com a Deriv encerrada.")
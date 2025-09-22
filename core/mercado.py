import json
import websockets
import asyncio
from collections import deque

class Mercado:
    def __init__(self, url, token, volatility_index):
        self.url = url
        self.token = token
        self.volatility_index = volatility_index
        self.precos = deque(maxlen=200)
        self.ws = None

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
        
        # 🚨 CORREÇÃO 🚨
        # Verificamos se a mensagem é um tick de preço em tempo real
        if 'tick' in data and 'symbol' in data['tick']:
            tick_data = data['tick']
            preco = float(tick_data['quote'])
            self.precos.append(preco)
            
            # Retornamos um dicionário completo, como esperado pelo treinar_modelo.py
            return {
                'price': preco,
                'msg_type': data.get('msg_type'),
                'symbol': tick_data.get('symbol'),
                'epoch': tick_data.get('epoch')
            }
        
        # Se a mensagem não for um tick de preço, retornamos None
        return None

    def get_precos(self):
        return list(self.precos)
        
    # 🚨 ADIÇÃO 🚨
    # Adicionamos o método desconectar() que o treinar_modelo.py precisa
    async def desconectar(self):
        if self.ws:
            await self.ws.close()
            print("🔌 Conexão com o Mercado Deriv fechada.")
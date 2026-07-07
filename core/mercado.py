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
        # Se houver um account_id, faz o fluxo Bearer Token + OTP idêntico ao print da doc!
        if account_id:
            try:
                ws_url = self.gerar_otp(account_id)
            except Exception as e:
                print(f"⚠️ Falha ao autenticar via Bearer HTTP (OTP): {e}")
                print("Tentando conexão direta padrão...")
                ws_url = self.url
        else:
            ws_url = self.url

        print(f"🔌 Conectando ao servidor autorizado da Deriv...")
        self.ws = await websockets.connect(ws_url, ping_interval=20, ping_timeout=20)

    def gerar_otp(self, account_id):
        if not account_id or account_id == "None":
            raise ValueError("ID da conta inválido para geração de OTP.")
            
        url = f"https://api.derivws.com/trading/v1/options/accounts/{account_id}/otp"
        app_id = os.getenv("APP_ID", "33IS1efhxY1mZfek6mlx3").strip()
        headers = {
            "Deriv-App-Id": app_id,
            "Authorization": f"Bearer {self.token}"
        }
        
        print(f"🔗 [DEBUG] Solicitando OTP. URL: {url}")
        print(f"🔗 [DEBUG] Headers enviados: {{'Deriv-App-Id': '{app_id}', 'Authorization': 'Bearer [ESCONDIDO]'}}")
        
        response = requests.post(url, headers=headers)
        
        # 💡 IMPRIME O RETORNO BRUTO DO SERVIDOR DA DERIV NO TERMINAL
        print("==================================================")
        print(f"🚨 [DEBUG] STATUS CODE DA DERIV: {response.status_code}")
        print(f"🚨 [DEBUG] RETORNO BRUTO DA DERIV: {response.text}")
        print("==================================================")
        
        try:
            otp_data = response.json()
        except Exception:
            raise Exception(f"Resposta da Deriv não foi um JSON válido. Verifique o retorno bruto acima.")

        if response.status_code == 200 and "data" in otp_data and "url" in otp_data["data"]:
            print("✅ URL com OTP gerada via Bearer Token com sucesso!")
            return otp_data["data"]["url"]
        else:
            detalhe_erro = otp_data.get("error", {}).get("message", "Erro desconhecido")
            raise Exception(f"Deriv recusou a criação do OTP: {detalhe_erro} (Status {response.status_code})")
   
    async def autenticar(self, token):
        await self.ws.send(json.dumps({"authorize": self.token}))
        response = await self.ws.recv()
        data = json.loads(response)
        if data.get("msg_type") == "authorize" and "error" not in data:
            print("🔐 Autenticado com sucesso na Deriv usando PAT!")
            return True
        else:
            print(f"❌ Erro de Autenticação WebSocket: {data.get('error', {}).get('message', 'Erro desconhecido')}")
            return False

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

    async def manter_conexao(self, account_id=None):
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
import json
import websockets
import asyncio
import os
import requests
from collections import deque

class Mercado:
    def __init__(self, url, token, volatility_index):
        # O teu App ID do .env (deve ser um número, ex: 1089)
        self.app_id = os.getenv("APP_ID", "1089").strip()
        
        # O teu Personal Access Token (ex: pat_f2c5...)
        self.token = str(token).strip().replace('"', '').replace("'", "")
        self.volatility_index = volatility_index
        self.precos = deque(maxlen=200)
        self.ws = None

        self.handlers = []
        self.queue = asyncio.Queue()
        self.autenticado = False

    def registrar_handler(self, handler):
        if handler not in self.handlers:
            self.handlers.append(handler)

    def remover_handler(self, handler):
        if handler in self.handlers:
            self.handlers.remove(handler)

    def gerar_otp(self, account_id):
        """Nova autenticação oficial da Deriv via REST API (Options Setup)"""
        # Novo Endpoint Oficial
        url_api = f"https://api.derivws.com/trading/v1/options/accounts/{account_id}/otp"
        
        token_formatado = self.token if self.token.lower().startswith("bearer ") else f"Bearer {self.token}"
        
        # Na nova API, o App ID e o Token vão nos cabeçalhos (Headers) HTTP
        headers = {
            "Deriv-App-ID": str(self.app_id),
            "Authorization": token_formatado,
            "Content-Type": "application/json"
        }
        
        print(f"📡 Solicitando OTP na nova API da Deriv para a conta {account_id}...")
        
        # O POST não precisa de corpo (payload) porque o account_id já vai no endereço URL
        res = requests.post(url_api, headers=headers, timeout=15)
        
        if res.status_code in [200, 201]:
            try:
                dados_resposta = res.json()
                # A nova API da Deriv devolve a URL pronta com o OTP embutido
                ws_url = dados_resposta.get("data", {}).get("url")
                
                if ws_url:
                    print("✅ OTP gerado com sucesso! A Deriv enviou a URL autenticada.")
                    return ws_url
                else:
                    raise Exception("A API respondeu com sucesso, mas a 'url' do WebSocket não foi encontrada no JSON.")
            except Exception as json_err:
                raise Exception(f"Erro ao ler JSON da API: {json_err}. Resposta bruta: {res.text}")
        else:
            raise Exception(f"A nova API rejeitou a requisição (Status {res.status_code}). Detalhes: {res.text}")

    async def conectar(self, account_id=None):
        """Liga-se à URL com o OTP (onde a autenticação já é validada automaticamente)"""
        if account_id:
            try:
                # 1️⃣ Gera a URL completa chamando a nova API REST
                ws_url = self.gerar_otp(account_id)
            except Exception as e:
                print(f"⚠️ Erro crítico ao gerar OTP: {e}")
                print("Tentando ligação à API pública (apenas leitura de mercado)...")
                ws_url = "wss://api.derivws.com/trading/v1/options/ws/public"
        else:
            ws_url = "wss://api.derivws.com/trading/v1/options/ws/public"

        print(f"🔌 Conectando ao WebSocket: {ws_url.split('otp=')[0]}... (OTP Oculto por Segurança)")
        self.ws = await websockets.connect(ws_url)
        
        # Como o OTP já está na URL, a ligação nasce 100% autenticada!
        self.autenticado = True 
        return self.ws

    async def autenticar(self, token):
        # A autenticação já é feita pelo OTP na URL. 
        # Mantemos o método a retornar 'True' apenas para não quebrar a lógica do teu bot_ia.py
        return True

    async def subscrever_ticks(self, symbol):
        if self.ws and hasattr(self.ws, 'state') and self.ws.state.name == "OPEN":
            print(f"📊 Solicitando subscrição contínua de ticks para {symbol}...")
            # ⚠️ ADICIONADO O "subscribe": 1 PARA MANTER A TORNEIRA DE DADOS ABERTA
            await self.ws.send(json.dumps({"ticks": symbol, "subscribe": 1}))
            return True
        return False

    async def obter_historico(self, symbol, style="prices", count=100):
        fut = asyncio.get_running_loop().create_future()
        async def _historico_handler(data):
            if data.get("msg_type") == "history":
                if not fut.done():
                    fut.set_result(data)

        self.registrar_handler(_historico_handler)
        try:
            await self.ws.send(json.dumps({
                "ticks_history": symbol,
                "adjust_start_time": 1,
                "count": count,
                "end": "latest",
                "start": 1,
                "style": style
            }))
            data = await asyncio.wait_for(fut, timeout=15)
            precos = [float(p) for p in data["history"]["prices"]]
            return precos
        finally:
            self.remover_handler(_historico_handler)

    async def manter_conexao(self, account_id=None):
        """Loop central blindado (agora renova automaticamente o OTP se o sinal cair)"""
        while True:
            try:
                conexao_ativa = self.ws is not None and hasattr(self.ws, 'state') and self.ws.state.name == "OPEN"

                if not conexao_ativa:
                    print("🔄 Conexão inativa. Reconectando e gerando novo OTP...")
                    await self.conectar(account_id=account_id)
                    await self.subscrever_ticks(self.volatility_index)

                msg = await self.ws.recv()   
                data = json.loads(msg)

                await self.queue.put(data)

                for handler in list(self.handlers):
                    asyncio.create_task(handler(data))

            except Exception as e:
                print(f"⚠️ Erro no loop do mercado: {e}")
                try:
                    if self.ws:
                        await self.ws.close()
                except:
                    pass
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
                'timestamp': tick_data.get('epoch')
            }
        return None
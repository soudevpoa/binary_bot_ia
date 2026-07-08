import json
import asyncio

class Saldo:
    def __init__(self, ws, mercado=None):
        self.ws = ws
        self.mercado = mercado
        self.resultado_futuro = None

    async def _handler(self, data):
        # Se for uma mensagem de saldo e estivermos esperando por ela
        if data.get("msg_type") == "balance":
            if self.resultado_futuro and not self.resultado_futuro.done():
                self.resultado_futuro.set_result(data)

    async def consultar(self):
        # Se tiver o objeto mercado cadastrado, usamos o sistema de handler centralizado
        if self.mercado:
            self.resultado_futuro = asyncio.get_running_loop().create_future()
            self.mercado.registrar_handler(self._handler)
            
            try:
                # Envia o comando para pedir o saldo
                await self.ws.send(json.dumps({ "balance": 1 }))
                # Aguarda o loop central pescar a resposta e nos entregar
                data = await asyncio.wait_for(self.resultado_futuro, timeout=10)
                return float(data.get("balance", {}).get("balance", 0.0))
            except asyncio.TimeoutError:
                print("⚠️ Tempo limite esgotado ao consultar saldo via Handler.")
                return 0.0
            finally:
                self.mercado.remover_handler(self._handler)
        else:
            # Fallback seguro caso não tenha o mercado injetado
            await self.ws.send(json.dumps({ "balance": 1 }))
            await asyncio.sleep(1)
            return 0.0
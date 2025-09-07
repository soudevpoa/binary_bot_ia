import json

class Saldo:
    def __init__(self, ws):
        self.ws = ws

    async def consultar(self):
        await self.ws.send(json.dumps({ "balance": 1 }))
        while True:
            response = await self.ws.recv()
            data = json.loads(response)
            if data.get("msg_type") == "balance":
                saldo = data["balance"]["balance"]
                print(f"💰 Saldo atual: {saldo:.2f}")
                return saldo
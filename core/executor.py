import asyncio
import json

class Executor:
    def __init__(self, ws, symbol, stake_base):
        self.ws = ws
        self.symbol = symbol
        self.stake_base = stake_base

    async def enviar_ordem(self, tipo, stake):
        contract_type = "CALL" if tipo == "CALL" else "PUT"
        ordem = {
            "buy": 1,
            "price": stake,
            "parameters": {
                "amount": stake,
                "basis": "stake",
                "contract_type": contract_type,
                "currency": "USD",
                "duration": 5,
                "duration_unit": "t",
                "symbol": self.symbol
            }
        }

        await self.ws.send(json.dumps(ordem))
        print(f"📤 Ordem enviada: {contract_type} | Stake: {stake:.2f}")

        # Aguarda confirmação da ordem
        contract_id = None
        while True:
            response = await self.ws.recv()
            data = json.loads(response)
            msg_type = data.get("msg_type")

            if msg_type == "buy":
                contract_id = data["buy"]["contract_id"]
                print(f"✅ Ordem executada! ID: {contract_id}")
                break
            else:
                print(f"📥 Ignorando mensagem: {msg_type}")

        # Aguarda resultado do contrato com tentativas e requisição ativa
        tentativas = 0
        try:
            while tentativas < 20:
                # Reenvia requisição de status do contrato
                await self.ws.send(json.dumps({
                    "proposal_open_contract": 1,
                    "contract_id": contract_id
                }))

                resultado_msg = await asyncio.wait_for(self.ws.recv(), timeout=10)
                resultado_data = json.loads(resultado_msg)
                msg_type = resultado_data.get("msg_type")
                print(f"📥 Recebido: {msg_type}")

                if msg_type == "proposal_open_contract":
                   contrato = resultado_data["proposal_open_contract"]

                # ✅ Insere aqui:
                vendido = contrato.get('is_sold', False)
                lucro = contrato.get('profit', 0)
                print(f"📦 Contrato recebido: vendido={vendido} | lucro={lucro}")

                if contrato.get("is_sold"):
                    profit = contrato.get("profit", 0)
                    if profit > 0:
                        print(f"🏆 WIN | Lucro: {profit:.2f}")
                        return "win"
                    else:
                        print(f"💥 LOSS | Prejuízo: {profit:.2f}")
                        return "loss"

                tentativas += 1
                await asyncio.sleep(1)

        except asyncio.TimeoutError:
            print("⏱️ Timeout ao aguardar resultado do contrato.")

        print("❌ Falha ao processar resultado da operação.")
        return "error"
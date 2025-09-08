import asyncio
import json
import random

class Executor:
    def __init__(self, ws, symbol, stake_base, simulacao_ativa=False):
        self.ws = ws
        self.symbol = symbol
        self.stake_base = stake_base
        self.simulacao_ativa = simulacao_ativa

    async def enviar_ordem(self, tipo, stake):
        # ✅ Verificação de stake mínima
        if stake < 0.35:
            print("⚠️ Stake abaixo do mínimo permitido pela Deriv.")
            return "error"

        # ✅ Validação do símbolo
        if not self.symbol.startswith("R_"):
            print(f"⚠️ Símbolo inválido: {self.symbol}")
            return "error"

        # ✅ Simulação avançada
        if self.simulacao_ativa:
            vendido = True
            lucro = round(random.uniform(-stake, stake * 1.5), 2)
            print(f"🧪 Simulação ativa | vendido={vendido} | lucro={lucro}")

            if lucro > 0:
                print(f"🏆 WIN | Lucro simulado: {lucro:.2f}")
                return "win"
            else:
                print(f"💥 LOSS | Prejuízo simulado: {lucro:.2f}")
                return "loss"

        # ✅ Envio real da ordem
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

        print("📦 Ordem preparada:", json.dumps(ordem, indent=2))
        await self.ws.send(json.dumps(ordem))

        response = await self.ws.recv()
        data = json.loads(response)

        if "error" in data:
            print(f"❌ Erro ao enviar ordem: {data['error']['message']}")
            return "error"

        # ✅ Aguarda confirmação da ordem
        contract_id = None
        while True:
            msg = await self.ws.recv()
            data = json.loads(msg)

            if "error" in data:
                print(f"❌ Erro na confirmação: {data['error']['message']}")
                return "error"

            msg_type = data.get("msg_type")
            if msg_type == "buy":
                contract_id = data["buy"]["contract_id"]
                print(f"✅ Ordem executada! ID: {contract_id}")
                break
            else:
                print(f"📥 Ignorando mensagem: {msg_type}")

        # ✅ Aguarda resultado do contrato
        contrato = None
        tentativas = 0
        try:
            while tentativas < 20:
                await self.ws.send(json.dumps({
                    "proposal_open_contract": 1,
                    "contract_id": contract_id
                }))

                resultado_msg = await asyncio.wait_for(self.ws.recv(), timeout=10)
                resultado_data = json.loads(resultado_msg)
                msg_type = resultado_data.get("msg_type")
                print(f"📥 Recebido: {msg_type}")

                if msg_type == "proposal_open_contract":
                    contrato = resultado_data.get("proposal_open_contract")

                if not contrato or not isinstance(contrato, dict):
                    print("⚠️ Contrato inválido ou não recebido.")
                    tentativas += 1
                    await asyncio.sleep(1)
                    continue

                vendido = contrato.get("is_sold", False)
                lucro = contrato.get("profit", 0)
                print(f"📦 Contrato recebido: vendido={vendido} | lucro={lucro}")

                if vendido:
                    if lucro > 0:
                        print(f"🏆 WIN | Lucro: {lucro:.2f}")
                        return "win"
                    else:
                        print(f"💥 LOSS | Prejuízo: {lucro:.2f}")
                        return "loss"

                tentativas += 1
                await asyncio.sleep(1)

        except asyncio.TimeoutError:
            print("⏱️ Timeout ao aguardar resultado do contrato.")

        print("❌ Falha ao processar resultado da operação.")
        return "error"
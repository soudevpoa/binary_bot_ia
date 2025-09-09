import json
import asyncio
from datetime import datetime

class Executor:
    def __init__(self, ws, symbol, stake):
        self.ws = ws
        self.symbol = symbol
        self.stake = stake

    async def enviar_ordem(self, direcao, stake):
        ordem = {
            "buy": 1,
            "price": stake,
            "parameters": {
                "amount": stake,
                "basis": "stake",
                "contract_type": direcao,
                "currency": "USD",
                "duration": 5,
                "duration_unit": "t",
                "symbol": self.symbol
            }
        }

        try:
            await self.ws.send(json.dumps(ordem))
            print(f"📥 Ordem preparada: {json.dumps(ordem, indent=2)}")

            contract_id = None

            # Aguarda confirmação de compra
            for _ in range(10):
                try:
                    msg = await asyncio.wait_for(self.ws.recv(), timeout=10)
                    data = json.loads(msg)
                except Exception as e:
                    print(f"⚠️ Erro ao receber resposta da ordem: {e}")
                    continue

                if data.get("msg_type") == "buy":
                    contract_id = data["buy"].get("contract_id")
                    print(f"📩 Confirmação de compra: {contract_id}")
                    break

            if not contract_id:
                print("❌ Falha ao obter contract_id.")
                return {"resultado": "erro_sem_contrato"}

            print(f"📡 Acompanhando contrato: {contract_id}")

            # Loop dedicado para aguardar expiração
            for tentativa in range(60):  # até 60 segundos
                await asyncio.sleep(2)

                # Reenvia requisição para obter status atualizado
                await self.ws.send(json.dumps({
                    "proposal_open_contract": 1,
                    "contract_id": contract_id
                }))

                try:
                    msg = await asyncio.wait_for(self.ws.recv(), timeout=10)
                    data = json.loads(msg)
                except Exception as e:
                    print(f"⚠️ Erro ao receber atualização do contrato: {e}")
                    continue

                if data.get("msg_type") == "proposal_open_contract":
                    contrato = data.get("proposal_open_contract", {})
                    status = contrato.get("status")
                    expirado = contrato.get("is_expired", False)
                    payout = contrato.get("payout", 0)

                    if expirado:
                        resultado = "win" if status == "won" else "loss" if status == "lost" else "erro_status_indefinido"
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                        print(f"📌 Contrato encerrado | Resultado: {resultado.upper()} | Payout: {payout}")
                        return {
                            "resultado": resultado,
                            "contract_id": contract_id,
                            "payout": payout,
                            "direcao": direcao,
                            "stake": stake,
                            "timestamp": timestamp
                        }

                    print(f"📊 Status atual do contrato: {status}")
                else:
                    print(f"📥 Ignorando mensagem irrelevante: {data.get('msg_type')}")

            print("⚠️ Tempo limite atingido sem expiração do contrato.")
            return {"resultado": "erro_timeout"}

        except Exception as e:
            print(f"❌ Erro ao enviar ordem: {e}")
            return {"resultado": "erro_conexao"}
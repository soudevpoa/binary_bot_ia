import json
import asyncio

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
            tentativas = 0

            while tentativas < 50:
                tentativas += 1

                try:
                    msg = await asyncio.wait_for(self.ws.recv(), timeout=30)
                except asyncio.TimeoutError:
                    print("⏱️ Tempo limite excedido esperando resultado.")
                    return "erro_timeout"
                except Exception as e:
                    print(f"⚠️ Erro ao receber resposta da ordem: {e}")
                    return "erro_conexao"

                try:
                    data = json.loads(msg)
                except Exception as e:
                    print(f"⚠️ Erro ao interpretar mensagem JSON: {e}")
                    continue

                # Confirmação de compra e captura do contract_id
                if data.get("msg_type") == "buy":
                    contract_id = data["buy"].get("contract_id")
                    print(f"📩 Confirmação de compra: {contract_id}")
                    if contract_id:
                        await asyncio.sleep(1)  # Garante que o contrato esteja ativo
                        await self.ws.send(json.dumps({
                            "proposal_open_contract": 1,
                            "contract_id": contract_id
                        }))
                        print(f"📡 Acompanhando contrato: {contract_id}")
                    continue

                # Verifica status final do contrato
                if data.get("msg_type") == "proposal_open_contract":
                    contrato = data.get("proposal_open_contract", {})
                    status = contrato.get("status")
                    if status == "won":
                        print("✅ Resultado recebido: WIN")
                        return "win"
                    elif status == "lost":
                        print("❌ Resultado recebido: LOSS")
                        return "loss"
                    else:
                        print(f"📊 Status atual do contrato: {status}")
                    continue

                print("📥 Ignorando mensagem irrelevante")

            print("⚠️ Número máximo de tentativas atingido sem resultado.")
            return "erro_sem_resultado"

        except Exception as e:
            print(f"❌ Erro ao enviar ordem: {e}")
            return "erro_conexao"
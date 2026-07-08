import json
import asyncio
from datetime import datetime

class Executor:
    def __init__(self, ws, symbol, stake_base, mercado):
        self.ws = ws
        self.symbol = symbol
        self.stake_base = stake_base
        self.mercado = mercado
        self.respostas = asyncio.Queue()

        # Registrar handler para capturar mensagens relevantes
        self.mercado.registrar_handler(self._handler)

    async def _handler(self, data):
        # Filtra mensagens de interesse
        if data.get("msg_type") in ["proposal", "buy", "proposal_open_contract"]:
            await self.respostas.put(data)

    async def enviar_ordem(self, direcao, stake):
        try:
            # 1️⃣ Solicita proposta
            proposta = {
                "proposal": 1,
                "amount": stake,
                "basis": "stake",
                "contract_type": direcao.upper(),
                "currency": "USD",
                "duration": 5,
                "duration_unit": "t",
                "underlying_symbol": self.symbol
            }
            await self.ws.send(json.dumps(proposta))

            # Aguarda a resposta filtrada pelo handler central
            data = await self.respostas.get()
            if data.get("msg_type") != "proposal" or "error" in data:
                return {"resultado": "erro_proposta"}

            proposta_data = data.get("proposal", {})
            id_proposta = proposta_data.get("id")

            # 2️⃣ Executa a compra do contrato baseado na proposta
            compra = {
                "buy": id_proposta,
                "price": stake
            }
            await self.ws.send(json.dumps(compra))

            data = await self.respostas.get()
            if data.get("msg_type") != "buy" or "error" in data:
                return {"resultado": "erro_compra"}

            contract_id = data.get("buy", {}).get("contract_id")
            print(f"🛒 Contrato comprado! ID: {contract_id} | Aguardando resultado...")

            # 3️⃣ Monitoramento do Contrato (Máximo de 60 tentativas)
            for _ in range(60):
                await asyncio.sleep(1)
                await self.ws.send(json.dumps({
                    "proposal_open_contract": 1,
                    "contract_id": contract_id
                }))
                
                data = await self.respostas.get()
                if data.get("msg_type") == "proposal_open_contract":
                    contrato = data.get("proposal_open_contract", {})
                    if contrato.get("is_expired") or contrato.get("status") in ["won", "lost"]:
                        status = contrato.get("status")
                        payout = contrato.get("payout", 0)
                        resultado = {"won": "win", "lost": "loss"}.get(status, status)
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
            
            print("⚠️ Tempo limite atingido sem expiração do contrato.")
            return {"resultado": "erro_timeout"}

        except Exception as e:
            print(f"❌ Erro ao enviar ordem: {e}")
            return {"resultado": "erro_conexao"}
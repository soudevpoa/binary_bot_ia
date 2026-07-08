import asyncio
import json
import os
import random
from datetime import datetime

# Importação dos Gerentes e Core
from core.gestores.stake_fixa import StakeFixa
from core.gestores.soros import Soros
from core.gestores.martingale_inteligente import MartingaleInteligente
from core.gestores.martingale_tradicional import MartingaleTradicional
from core.logger import Logger
from core.mercado import Mercado
from core.executor import Executor
from core.saldo import Saldo
from core.desempenho import Desempenho
from core.probabilidade_estatistica import ProbabilidadeEstatistica
from indicadores.indicadores import calcular_volatilidade

class BotBase:
    def __init__(self, config, token, estrategia, estatisticas_file):
        self.config = config
        self.token = token
        self.estrategia = estrategia # Ex: Instância de bot_mm, bot_rsi, etc.
        self.prices = []
        self.sequencia_resultados = []
        self.loss_virtual_ativa = config.get("usar_loss_virtual", False)
        self.limite_loss_virtual = int(config.get("limite_loss_virtual", 4))
        self.contador_loss_virtual = 0
        self.modo_simulacao = config.get("modo_simulacao", False)
        
        self.mercado = None
        self.executor = None
        self.saldo = None
        self.painel = None
        self.logger = Logger()
        self.estatistica = ProbabilidadeEstatistica(estatisticas_file)

        # Configuração Dinâmica do Gerenciamento de Banca
        gestao_tipo = config.get("gestao_banca", "martingale_inteligente").lower()
        stake_base = max(config.get("stake", 0.35), 0.35)
        
        if gestao_tipo == "stake_fixa":
            self.gestor = StakeFixa(stake_base)
        elif gestao_tipo == "soros":
            self.gestor = Soros(stake_base, config.get("soros_nivel_maximo", 2))
        elif gestao_tipo == "martingale_tradicional":
            self.gestor = MartingaleTradicional(stake_base, config.get("multiplicador_martingale", 2.0), config.get("max_martingales", 5))
        else:
            self.gestor = MartingaleInteligente(stake_base, config.get("multiplicador_martingale", 2.0), config.get("max_martingales", 5))

    async def iniciar(self, account_id=None):
        try:
            # 1. Instancia o Mercado
            self.mercado = Mercado("wss://api.derivws.com/trading/v1/options/ws/public", self.token, self.config["volatility_index"])
            
            # 2. Conexão Nativa com OTP (via nova API REST)
            await self.mercado.conectar(account_id=account_id)
            
            # 3. Dispara o Loop Central em segundo plano e previne conflitos de recv()
            asyncio.create_task(self.mercado.manter_conexao(account_id=account_id))
            await asyncio.sleep(1) # Dá um segundo para o loop respirar e arrancar
            
            # 4. Subscreve aos ticks de forma contínua ("subscribe": 1)
            await self.mercado.subscrever_ticks(self.config["volatility_index"])

            # 5. Instancia Saldo e Executor conectados ao Mercado global
            self.executor = Executor(self.mercado.ws, self.config["volatility_index"], self.gestor.get_stake(), self.mercado)
            self.saldo = Saldo(self.mercado.ws, mercado=self.mercado)

            saldo_inicial = await self.saldo.consultar()
            self.painel = Desempenho(stake_base=self.gestor.get_stake())

            # Metas e limites
            meta_lucro = self.config.get("meta_lucro", saldo_inicial * self.config.get("meta_lucro_percentual", 0.10))
            stop_loss = self.config.get("stop_loss", saldo_inicial * self.config.get("stop_loss_percentual", 0.05))

            self.logger.log("INFO", f"🤖 Base do Robô iniciada para {self.config['volatility_index']} | Estratégia: {self.estrategia.__class__.__name__} | Saldo: ${saldo_inicial:.2f}")

            # ==============================
            # LOOP PRINCIPAL DE OPERAÇÕES
            # ==============================
            while True:
                # Gestão de Janelas de Horário
                if self.config.get("usar_janela_horario", False):
                    janelas_config = self.config.get("janelas_horario", [])
                    agora = datetime.now().time()
                    janelas = []
                    for janela in janelas_config:
                        try:
                            inicio = datetime.strptime(janela["inicio"], "%H:%M").time()
                            fim = datetime.strptime(janela["fim"], "%H:%M").time()
                            janelas.append((inicio, fim))
                        except Exception:
                            continue
                    
                    if not any(inicio <= agora <= fim for inicio, fim in janelas):
                        self.logger.log("INFO", "⏳ Fora da janela de operação. Aguardando...")
                        await asyncio.sleep(60)
                        continue

                try:
                    # 6. Escuta a fila central do mercado (Zero conflito de recv)
                    msg_data = await self.mercado.queue.get()
                    self.mercado.queue.task_done()
                except Exception as e:
                    self.logger.log("ERROR", f"⚠️ Erro ao colher dados da fila: {e}")
                    await asyncio.sleep(2)
                    continue

                data = self.mercado.processar_tick(msg_data)
                if not data:
                    continue

                price = data["price"]
                self.prices.append(price)

                # 7. TRAVA DE AQUECIMENTO UNIVERSAL
                if len(self.prices) < 30:
                    print(f"⏳ A aquecer os indicadores ({len(self.prices)}/30)... Preço atual: {price}")
                    continue
                
                if len(self.prices) > 60:
                    self.prices.pop(0)

                # 8. Delega a decisão de Call/Put para o algoritmo específico que herdou esta base
                sinal, padrao = self.estrategia.analisar(self.prices)

                if sinal:
                    saldo_atual = await self.saldo.consultar()
                    stake = self.gestor.get_stake()

                    self.logger.log("INFO", f"🔔 Sinal de entrada detetado: {sinal} pelo padrão {padrao} | 💰 Stake: {stake:.2f}")

                    if self.modo_simulacao:
                        resultado = random.choice(["win", "loss"])
                        self.logger.log("INFO", f"🧪 Modo de Simulação Ativo | Resultado Sorteado: {resultado}")
                        resposta = {
                            "resultado": resultado,
                            "payout": stake * 0.95,
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "direcao": sinal,
                            "stake": stake,
                            "contract_id": "simulado_123"
                        }
                    else:
                        resposta = await self.executor.enviar_ordem(sinal, stake)
                    resultado_final = resposta.get("resultado")
                        # Se o contrato estiver OPEN, esperamos 2 segundos e verificamos de novo
                    if resposta.get("resultado") == "OPEN":
                        self.logger.log("INFO", "⏳ Contrato OPEN. Aguardando 3 segundos para confirmar resultado...")
                        await asyncio.sleep(3)
                        # Aqui você pode chamar uma função de 'verificar_status' se o seu executor tiver
                        # Por enquanto, apenas seguimos para o próximo ciclo para ele reprocessar
                        continue

                    if resultado_final not in ["win", "loss"]:
                        self.logger.log("ERROR", f"⚠️ Status desconhecido recebido: {resultado_final}")
                        continue

                    # Agora sim, finaliza a operação com segurança
                    await self._finalizar_operacao(resultado_final, stake, padrao, sinal, price, resposta)

                    valido, motivo = self._validar_resposta(resposta)
                    if not valido:
                        self.logger.log("ERROR", f"⚠️ Resposta do contrato inválida: {motivo}")
                        continue

                    resultado = resposta["resultado"]
                    
                    # Processa Win/Loss no Saldo e no Gestor (Martingale, Soros, etc.)
                    await self._finalizar_operacao(resultado, stake, padrao, sinal, price, resposta)

                    # Verifica as Metas e para o Robô se as atingir
                    saldo_final = await self.saldo.consultar()
                    lucro_total = saldo_final - saldo_inicial
                    
                    if lucro_total >= meta_lucro:
                        self.logger.log("INFO", f"🎯 Meta de lucro atingida com sucesso: +${lucro_total:.2f}")
                        break
                    if lucro_total <= -stop_loss:
                        self.logger.log("INFO", f"🛑 Stop loss atingido de forma segura: -${abs(lucro_total):.2f}")
                        break

                    await asyncio.sleep(10) # Aguarda após a operação para limpar a cabeça do mercado
        
        except Exception as e:
            self.logger.log("ERROR", f"Erro crítico na execução base do Bot: {e}")
        finally:
            self.logger.log("INFO", "A desligar bot e a gravar relatórios de desempenho...")
            if hasattr(self, 'estatistica'):
                self.estatistica.salvar_estatisticas()
            self.logger.log("INFO", "Bot completamente encerrado.")

    def _validar_resposta(self, resposta):
        if not isinstance(resposta, dict):
            return False, "resposta_invalida"
        
        resultado = resposta.get("resultado")
        if resultado not in ["win", "loss"]:
            return False, f"status_{resultado}" # Retorna o status para sabermos o que aconteceu
            
        if not self.modo_simulacao and resposta.get("contract_id") is None:
            return False, "contrato_nao_executado"
            
        return True, "ok"

    async def _finalizar_operacao(self, resultado, stake, padrao, direcao, price, resposta):
        saldo_atual = await self.saldo.consultar()
        
        if hasattr(self.gestor, 'registrar_resultado'):
            self.gestor.registrar_resultado(resultado)
            
        self.painel.registrar_resultado(resultado, stake)
        self.estatistica.registrar_operacao(padrao, resultado)
        
        taxa = self.estatistica.calcular_taxa_acerto(padrao)
        self.logger.log("INFO", f"📈 Taxa de acerto para '{padrao}': {taxa}%")
        self.logger.registrar(direcao, price, None, None, None, stake)
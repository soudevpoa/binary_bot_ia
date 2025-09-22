import json
import os

class ProbabilidadeEstatistica:
    def __init__(self, file_path):
        # 🚨 AJUSTE 1: Removemos o valor fixo e usamos o caminho que é passado
        self.file_path = file_path
        self.estatisticas = self.carregar_estatisticas()
        
    def carregar_estatisticas(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r') as f:
                return json.load(f)
        return {}
        
    def salvar_estatisticas(self):
        with open(self.file_path, 'w') as f:
            json.dump(self.estatisticas, f, indent=4)
            
    # 🚨 AJUSTE 2: Adicionamos o argumento 'padrao' para registrar a origem da operação
    def registrar_operacao(self, padrao, resultado):
        if padrao not in self.estatisticas:
            self.estatisticas[padrao] = {
                "total": 0,
                "win": 0,
                "loss": 0,
                "taxa_acerto": 0.0
            }
        
        self.estatisticas[padrao]["total"] += 1
        
        if resultado == "win":
            self.estatisticas[padrao]["win"] += 1
        elif resultado == "loss":
            self.estatisticas[padrao]["loss"] += 1
            
        # Recalcula a taxa de acerto para o padrão
        if self.estatisticas[padrao]["total"] > 0:
            self.estatisticas[padrao]["taxa_acerto"] = (
                self.estatisticas[padrao]["win"] / self.estatisticas[padrao]["total"]
            ) * 100
        
        self.salvar_estatisticas()
        
    def calcular_taxa_acerto(self, padrao):
        estatisticas_padrao = self.estatisticas.get(padrao, None)
        if estatisticas_padrao and estatisticas_padrao["total"] > 0:
            return estatisticas_padrao["taxa_acerto"]
        return 0.0
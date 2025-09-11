import json
import os

class ProbabilidadeEstatistica:
    def __init__(self, nome_arquivo):
        self.nome_arquivo = nome_arquivo
        self.dados = self._carregar_dados()

    def _carregar_dados(self):
        if os.path.exists(self.nome_arquivo):
            try:
                with open(self.nome_arquivo, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def _salvar_dados(self):
        try:
            with open(self.nome_arquivo, 'w') as f:
                json.dump(self.dados, f, indent=4)
        except IOError as e:
            print(f"Erro ao salvar o arquivo de estatísticas: {e}")

    def registrar_operacao(self, direcao, resultado, padrao):
        if padrao not in self.dados:
            self.dados[padrao] = {"win": 0, "loss": 0}
        
        if resultado == "win":
            self.dados[padrao]["win"] += 1
        elif resultado == "loss":
            self.dados[padrao]["loss"] += 1
        
        self._salvar_dados() # Chama a função para salvar os dados

    def calcular_taxa_acerto(self, padrao):
        if padrao not in self.dados:
            return 0
        
        wins = self.dados[padrao]["win"]
        losses = self.dados[padrao]["loss"]
        total = wins + losses
        
        if total == 0:
            return 0
        
        taxa = (wins / total) * 100
        return round(taxa, 2)
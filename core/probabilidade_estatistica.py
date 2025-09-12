import json
import os

class ProbabilidadeEstatistica:
    def __init__(self, estatisticas_file):
        
        self.estatisticas_file = estatisticas_file
        self.estatisticas = self.carregar_estatisticas()
    
    def carregar_estatisticas(self):
        """Carrega as estatísticas do arquivo, ou retorna um dicionário vazio."""
        
        caminho_completo = os.path.join("estatisticas", self.estatisticas_file)
        
        if os.path.exists(caminho_completo):
            try:
                with open(caminho_completo, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                print(f"⚠️ Erro ao ler o arquivo de estatísticas {caminho_completo}. Criando novo.")
                return {}
        return {}

    def salvar_estatisticas(self):
        """Salva as estatísticas atuais em um arquivo JSON."""
        # Cria a pasta 'estatisticas' se ela não existir
        os.makedirs("estatisticas", exist_ok=True)
        caminho_completo = os.path.join("estatisticas", self.estatisticas_file)
        
        try:
            with open(caminho_completo, "w") as f:
                json.dump(self.estatisticas, f, indent=4)
            print(f"✅ Estatísticas salvas em {caminho_completo}")
        except IOError as e:
            print(f"❌ Erro ao salvar o arquivo de estatísticas: {e}")

    def registrar_operacao(self, direcao, resultado, padrao):
        # AQUI ESTÁ A CORREÇÃO: Removemos a chamada para o método de salvar
        if padrao not in self.estatisticas:
            self.estatisticas[padrao] = {"wins": 0, "losses": 0}
        
        if resultado == "win":
            self.estatisticas[padrao]["wins"] += 1
        elif resultado == "loss":
            self.estatisticas[padrao]["losses"] += 1
    
    def calcular_taxa_acerto(self, padrao):
        if padrao not in self.estatisticas:
            return 0
        
        wins = self.estatisticas[padrao].get("wins", 0)
        losses = self.estatisticas[padrao].get("losses", 0)
        total = wins + losses
        
        if total == 0:
            return 0
        
        taxa = (wins / total) * 100
        return round(taxa, 2)
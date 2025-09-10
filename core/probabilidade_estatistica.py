import json
import os

class ProbabilidadeEstatistica:
    def __init__(self, filename="dados/estatisticas.json"):
        self.filename = filename
        self.historico = []
        self.carregar_historico()

    def carregar_historico(self):
        if os.path.exists(self.filename):
            with open(self.filename, "r") as f:
                try:
                    self.historico = json.load(f)
                    print(f"✅ Histórico de estatísticas carregado de {self.filename}")
                except json.JSONDecodeError:
                    print("⚠️ Erro ao carregar o arquivo de estatísticas. Iniciando um novo histórico.")
                    self.historico = []
    
    def salvar_historico(self):
        try:
            with open(self.filename, "w") as f:
                json.dump(self.historico, f, indent=2)
            print(f"💾 Histórico de estatísticas salvo em {self.filename}")
        except Exception as e:
            print(f"❌ Erro ao salvar o histórico de estatísticas: {e}")

    def registrar_operacao(self, tipo, resultado, padrao):
        self.historico.append({
            "tipo": tipo,
            "resultado": resultado,
            "padrao": padrao
        })
        self.salvar_historico() # Salva a cada nova operação

    def calcular_taxa_acerto(self, padrao=None):
        if not self.historico:
            return 0.0

        filtrado = self.historico if padrao is None else [
            h for h in self.historico if h["padrao"] == padrao
        ]

        if not filtrado:
            return 0.0

        acertos = sum(1 for h in filtrado if h["resultado"] == "win")
        taxa = acertos / len(filtrado)
        return round(taxa * 100, 2)

    def get_total_operacoes(self, padrao=None):
        if padrao is None:
            return len(self.historico)
        
        count = sum(1 for h in self.historico if h["padrao"] == padrao)
        return count

    def padroes_mais_lucrativos(self, top_n=3):
        padroes = {}
        for h in self.historico:
            padrao = h["padrao"]
            if padrao not in padroes:
                padroes[padrao] = {"total": 0, "wins": 0}
            padroes[padrao]["total"] += 1
            if h["resultado"] == "win":
                padroes[padrao]["wins"] += 1

        estatisticas = [
            (padrao, round((dados["wins"] / dados["total"]) * 100, 2))
            for padrao, dados in padroes.items()
        ]

        estatisticas.sort(key=lambda x: x[1], reverse=True)
        return estatisticas[:top_n]
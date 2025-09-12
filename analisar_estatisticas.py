import os
import json
from tabulate import tabulate

def analisar_estatisticas():
    """Lê todos os arquivos de estatísticas e gera um resumo."""
    
    print("📊 Analisando as estatísticas dos bots...")
    
    resultados_globais = []
    
    # Percorre todos os arquivos na pasta principal
    for nome_arquivo in os.listdir("."):
        if nome_arquivo.startswith("estatisticas_") and nome_arquivo.endswith(".json"):
            try:
                with open(nome_arquivo, "r") as f:
                    dados = json.load(f)
                    
                    nome_bot = nome_arquivo.replace("estatisticas_", "").replace(".json", "")
                    
                    # Usa .get() para evitar o KeyError
                    total_operacoes = dados.get("total_operacoes", 0)
                    vitorias = dados.get("vitorias", 0)
                    derrotas = dados.get("derrotas", 0)
                    meta_batida = dados.get("meta_batida", False)
                    lucro_total = dados.get("lucro_total", 0)

                    if not total_operacoes:
                        taxa_acerto = 0
                    else:
                        taxa_acerto = (vitorias / total_operacoes) * 100
                    
                    # Formata os dados para exibição
                    resultados_globais.append([
                        nome_bot,
                        total_operacoes,
                        vitorias,
                        derrotas,
                        meta_batida,
                        f"{taxa_acerto:.2f}%",
                        f"R${lucro_total:.2f}"
                    ])
                    
            except (IOError, json.JSONDecodeError) as e:
                print(f"⚠️ Erro ao ler o arquivo {nome_arquivo}: {e}")
                continue

    if not resultados_globais:
        print("❌ Nenhum arquivo de estatísticas encontrado. Execute os bots primeiro para gerar os arquivos.")
        return

    # Imprime a tabela com os resultados
    headers = ["Bot", "Total Ops", "Vitórias", "Derrotas", "Meta Batida?", "Taxa de Acerto", "Lucro Total"]
    print("\n--- Resumo de Desempenho dos Bots ---")
    print(tabulate(resultados_globais, headers=headers, tablefmt="fancy_grid"))
    
    print("\n✅ Análise concluída.")

if __name__ == "__main__":
    analisar_estatisticas()
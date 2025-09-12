import json
import os
import sys

def carregar_estatisticas(nome_arquivo):
    """
    Carrega as estatísticas de um arquivo JSON.
    """
    caminho_completo = os.path.join("estatisticas", nome_arquivo)
    
    try:
        with open(caminho_completo, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"⚠️ Erro: O arquivo '{caminho_completo}' não foi encontrado.")
        return None
    except json.JSONDecodeError:
        print(f"⚠️ Erro: O arquivo '{caminho_completo}' não é um JSON válido.")
        return None

def analisar_estatisticas(estatisticas):
    """
    Analisa e exibe as estatísticas para cada padrão.
    """
    if not estatisticas:
        print("Nenhuma estatística para analisar.")
        return

    print("📊 Análise das Estatísticas de Padrões")
    print("-" * 30)
    
    for padrao, dados in estatisticas.items():
        # Calcula o total de operações aqui
        total_ops = dados.get("wins", 0) + dados.get("losses", 0)
        
        if total_ops > 0:
            taxa_acerto = (dados.get('wins', 0) / total_ops) * 100
            print(f"Padrão: {padrao}")
            print(f"  Total de Ops: {total_ops}")
            print(f"  Wins: {dados.get('wins', 0)}")
            print(f"  Losses: {dados.get('losses', 0)}")
            print(f"  Taxa de Acerto: {taxa_acerto:.2f}%")
            print("-" * 30)
        else:
            print(f"Padrão: {padrao} - Nenhuma operação registrada.")
            print("-" * 30)

def main():
    # Verifica se o nome do arquivo foi passado como argumento
    if len(sys.argv) < 2:
        print("⚠️ Erro: Por favor, forneça o nome do arquivo de estatísticas.")
        print("Exemplo de uso: python analisar_estatisticas.py estatisticas_rsi_bollinger.json")
        return

    # AQUI ESTÁ A MÁGICA: Pega o nome do arquivo do primeiro argumento
    nome_arquivo = sys.argv[1]

    estatisticas = carregar_estatisticas(nome_arquivo)
    
    if estatisticas:
        analisar_estatisticas(estatisticas)

if __name__ == "__main__":
    main()
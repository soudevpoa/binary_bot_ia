import numpy as np
from sklearn.linear_model import LogisticRegression
import joblib
import os

class ModeloIA:
    def __init__(self, modelo_path="modelo_ia.pkl"):
        self.modelo = None
        self.modelo_path = os.path.join("dados", modelo_path)
        self.carregar_modelo()

    def carregar_modelo(self):
        """Carrega o modelo de IA a partir de um arquivo, se ele existir."""
        if os.path.exists(self.modelo_path):
            self.modelo = joblib.load(self.modelo_path)
            print("🧠 Modelo de IA carregado com sucesso!")
        else:
            print("⚠️ Nenhum modelo de IA encontrado. Ele será treinado ao receber dados.")
    
    def salvar_modelo(self):
        """Salva o modelo de IA em um arquivo para uso futuro."""
        if self.modelo is not None:
            # Cria o diretório 'dados' se não existir
            os.makedirs(os.path.dirname(self.modelo_path), exist_ok=True)
            joblib.dump(self.modelo, self.modelo_path)
            print("💾 Modelo de IA salvo com sucesso!")

    def treinar(self, features, labels):
        """
        Treina o modelo de IA com os dados fornecidos.
        
        Args:
            features (np.array): O array de características (RSI, MM, etc.).
            labels (np.array): O array com os resultados (up/down).
        """
        if len(features) < 100:
            print("⏳ Dados insuficientes para treinamento. Mínimo de 100 amostras.")
            return False

        print(f"📈 Treinando o modelo com {len(features)} amostras...")
        self.modelo = LogisticRegression(max_iter=1000)
        self.modelo.fit(features, labels)
        self.salvar_modelo()
        print("✅ Treinamento concluído!")
        return True

    def prever(self, features):
        """
        Faz uma previsão usando o modelo treinado.
        
        Args:
            features (np.array): As características do momento atual para a previsão.
            
        Returns:
            str: "up" ou "down" baseado na previsão. Retorna "neutro" se o modelo não estiver treinado.
        """
        if self.modelo is None:
            return "neutro"
            
        previsao = self.modelo.predict(features.reshape(1, -1))
        return previsao[0]
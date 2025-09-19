import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.optimizers import Adam
from sklearn.preprocessing import StandardScaler

class ModeloNeural:
    def __init__(self):
        self.scaler = StandardScaler()
        self.model = Sequential([
            Dense(8, input_dim=4, activation='relu'),
            Dense(4, activation='relu'),
            Dense(1, activation='sigmoid')
        ])
        self.model.compile(optimizer=Adam(learning_rate=0.001), loss='binary_crossentropy', metrics=['accuracy'])

    def treinar(self, X, y, epochs=50):
        
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y, epochs=epochs, verbose=0)


    def prever(self, features):
        
        features_scaled = self.scaler.transform(features)
        prob = self.model.predict(features_scaled, verbose=0)[0][0]
        return "up" if prob > 0.5 else "down"

    def prever_lote(self, X):
        X_scaled = self.scaler.transform(X)
        probs = self.model.predict(X_scaled, verbose=0).flatten()
        return ["up" if p > 0.5 else "down" for p in probs]
    
    def salvar_modelo(self, caminho="modelo_megalodon.h5"):
        self.model.save(caminho)

    def carregar_modelo(self, caminho="modelo_megalodon.h5"):
        from tensorflow.keras.models import load_model
        self.model = load_model(caminho)

    def carregar_scaler(self, caminho="scaler_megalodon.pkl"):
        import joblib
        self.scaler = joblib.load(caminho)
        if not hasattr(self.scaler, "mean_"):
            raise ValueError("⚠️ Scaler carregado, mas não está ajustado. Execute o treino novamente.")




import keras
from keras.models import Sequential
from keras.layers import Dense, Dropout
from keras.optimizers import Adam
import joblib


class ModeloNeural:
    def __init__(self, input_shape):
        self.input_shape = input_shape
        self.modelo = self._construir_modelo()
        self.scaler = None
        self.acuracia = 0.0

    def _construir_modelo(self):
        modelo = Sequential([
            Dense(64, activation='relu', input_shape=(self.input_shape,)),
            Dropout(0.2),
            Dense(32, activation='relu'),
            Dropout(0.2),
            Dense(1, activation='sigmoid')
        ])
        modelo.compile(optimizer='adam',
                       loss='binary_crossentropy', metrics=['accuracy'])
        return modelo

    def treinar(self, x_treino, y_treino, x_teste, y_teste, epochs=100, batch_size=32):
        print("🧠 Treinando modelo...")
        historico = self.modelo.fit(
            x_treino,
            y_treino,
            epochs=epochs,
            batch_size=batch_size,
            validation_data=(x_teste, y_teste),
            verbose=1
        )
        self.acuracia = historico.history['accuracy'][-1] * 100
        print("✅ Treinamento concluído.")

    def salvar(self, file_path):
        self.modelo.save(file_path)

    def carregar(self, file_path):
        self.modelo = keras.saving.load_model(file_path)

    def salvar_scaler(self, file_path):
        joblib.dump(self.scaler, file_path)

    def carregar_scaler(self, file_path):
        self.scaler = joblib.load(file_path)

    def prever(self, dados_normalizados):
        previsao = self.modelo.predict(dados_normalizados)
        return previsao[0][0]

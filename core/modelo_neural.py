import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.optimizers import Adam

class ModeloNeural:
    def __init__(self):
        self.model = Sequential([
            Dense(8, input_dim=4, activation='relu'),
            Dense(4, activation='relu'),
            Dense(1, activation='sigmoid')
        ])
        self.model.compile(optimizer=Adam(learning_rate=0.001), loss='binary_crossentropy', metrics=['accuracy'])

    def treinar(self, X, y, epochs=50):
        self.model.fit(X, y, epochs=epochs, verbose=0)

    def prever(self, features):
        prob = self.model.predict(features, verbose=0)[0][0]
        return "up" if prob > 0.5 else "down"

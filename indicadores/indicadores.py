import pandas as pd
import numpy as np

def calcular_rsi(prices, period=14):
    """
    Calcula o RSI (Índice de Força Relativa) para uma lista de preços.
    """
    df = pd.DataFrame(prices, columns=["close"])
    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    # Usa média móvel exponencial para uma resposta mais rápida
    avg_gain = gain.ewm(com=period - 1, adjust=False).mean()
    avg_loss = loss.ewm(com=period - 1, adjust=False).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi.iloc[-1]

def calcular_mm(prices, period):
    """
    Calcula a Média Móvel Simples (SMA) para uma lista de preços.
    """
    if len(prices) < period:
        return None
    return sum(prices[-period:]) / period

def calcular_volatilidade(prices):
    """
    Calcula o desvio padrão de uma lista de preços para medir a volatilidade.
    """
    if len(prices) < 2:
        return 0.0
    return np.std(prices)

def calcular_bb(prices, period=20):
    """
    Calcula as Bandas de Bollinger (média móvel e desvios padrão superior e inferior).
    """
    df = pd.DataFrame(prices, columns=["close"])
    sma = df["close"].rolling(window=period).mean()
    std = df["close"].rolling(window=period).std()
    
    if std.iloc[-1] is np.nan:
        return None, None
    
    upper = sma.iloc[-1] + (2 * std.iloc[-1])
    lower = sma.iloc[-1] - (2 * std.iloc[-1])
    return lower, upper
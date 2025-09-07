import pandas as pd

def calcular_rsi(prices, period=14):
    df = pd.DataFrame(prices, columns=["close"])
    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

def calcular_bb(prices, period=20):
    df = pd.DataFrame(prices, columns=["close"])
    sma = df["close"].rolling(window=period).mean()
    std = df["close"].rolling(window=period).std()
    upper = sma.iloc[-1] + (2 * std.iloc[-1])
    lower = sma.iloc[-1] - (2 * std.iloc[-1])
    return lower, upper
import numpy as np

def detect_rsi_divergence(df, direction, lookback=20):

    if len(df) < lookback + 5:
        return False

    closes = df["close"].values
    rsi = df["rsi"].values

    recent_prices = closes[-lookback:]
    recent_rsi = rsi[-lookback:]

    # LONG için bullish divergence
    if direction == "LONG":

        price_low1 = np.min(recent_prices[:-5])
        price_low2 = np.min(recent_prices[-5:])

        rsi_low1 = np.min(recent_rsi[:-5])
        rsi_low2 = np.min(recent_rsi[-5:])

        # fiyat lower low ama RSI higher low
        if price_low2 < price_low1 and rsi_low2 > rsi_low1:
            return True

    # SHORT için bearish divergence
    if direction == "SHORT":

        price_high1 = np.max(recent_prices[:-5])
        price_high2 = np.max(recent_prices[-5:])

        rsi_high1 = np.max(recent_rsi[:-5])
        rsi_high2 = np.max(recent_rsi[-5:])

        # fiyat higher high ama RSI lower high
        if price_high2 > price_high1 and rsi_high2 < rsi_high1:
            return True

    return False
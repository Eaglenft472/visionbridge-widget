import numpy as np

def detect_support_resistance(df, lookback=50):

    highs = df["high"].values[-lookback:]
    lows = df["low"].values[-lookback:]

    resistance = np.max(highs[:-5])
    support = np.min(lows[:-5])

    return support, resistance


def detect_break_and_retest(df, direction):

    support, resistance = detect_support_resistance(df)

    last = df.iloc[-1]
    prev = df.iloc[-2]

    close = last["close"]
    prev_close = prev["close"]

    # LONG → resistance kırılımı + kapanış üstünde
    if direction == "LONG":

        if prev_close <= resistance and close > resistance:
            return True

    # SHORT → support kırılımı + kapanış altında
    if direction == "SHORT":

        if prev_close >= support and close < support:
            return True

    return False
# ================= PATTERN ENGINE v4 =================

def detect_engulfing(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]

    # Bullish engulfing: Mevcut mum yeşil, önceki kırmızı ve mevcut mum öncekini tamamen yutuyor
    if prev["close"] < prev["open"] and last["close"] > last["open"]:
        if last["close"] > prev["open"] and last["open"] < prev["close"]:
            return "BULL"

    # Bearish engulfing: Mevcut mum kırmızı, önceki yeşil ve mevcut mum öncekini tamamen yutuyor
    if prev["close"] > prev["open"] and last["close"] < last["open"]:
        if last["open"] > prev["close"] and last["close"] < prev["open"]:
            return "BEAR"

    return None


def detect_pinbar(df):
    last = df.iloc[-1]

    body = abs(last["close"] - last["open"])
    upper_wick = last["high"] - max(last["close"], last["open"])
    lower_wick = min(last["close"], last["open"]) - last["low"]

    if body == 0: return None

    # Bullish pin: Alt gölge gövdenin en az 2 katı ve üst gölge küçük olmalı
    if lower_wick > body * 2 and upper_wick < body:
        return "BULL"

    # Bearish pin: Üst gölge gövdenin en az 2 katı ve alt gölge küçük olmalı
    if upper_wick > body * 2 and lower_wick < body:
        return "BEAR"

    return None


def pattern_score(df, direction):
    """
    Direction: 'LONG' veya 'SHORT' (structure_engine'den gelir)
    Puanlar Enterprise v4'teki 0.85 eşiğine katkı sağlar.
    """
    score = 0
    engulf = detect_engulfing(df)
    pin = detect_pinbar(df)

    # LONG Onayları
    if direction == "LONG":
        if engulf == "BULL": score += 0.15 # Engulfing güçlü bir trend devam sinyalidir
        if pin == "BULL": score += 0.10   # Pinbar bir geri dönüş/tepki sinyalidir

    # SHORT Onayları
    if direction == "SHORT":
        if engulf == "BEAR": score += 0.15
        if pin == "BEAR": score += 0.10

    return score
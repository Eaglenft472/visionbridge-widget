# ================= REGIME AGGRESSION ENGINE =================

def regime_aggression_adjustment(df, base_risk):

    atr = df.iloc[-1]["atr"]
    atr_prev = df.iloc[-5]["atr"]

    ema20 = df.iloc[-1]["ema20"]
    ema50 = df.iloc[-1]["ema50"]

    volatility_expanding = atr > atr_prev * 1.2
    trend_strength = abs(ema20 - ema50) / ema50

    # ===== STRONG TREND =====
    if trend_strength > 0.01 and volatility_expanding:
        return base_risk * 1.4

    # ===== CHOP =====
    if trend_strength < 0.003:
        return base_risk * 0.6

    # ===== NORMAL =====
    return base_risk
def rotation_filter(df, stats):

    score_bonus = 0

    # Momentum kontrolü (EMA farkı)
    ema_gap = df.iloc[-1]["ema20"] - df.iloc[-1]["ema50"]

    if abs(ema_gap) > df.iloc[-1]["atr"]:
        score_bonus += 0.1

    # Equity uyumu
    if stats and stats.get("expectancy", 0) > 0:
        score_bonus += 0.05

    # RSI momentum
    rsi = df.iloc[-1]["rsi"]
    if rsi > 60 or rsi < 40:
        score_bonus += 0.05

    return score_bonus
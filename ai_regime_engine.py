# ================= AI REGIME ENGINE =================
import numpy as np

def ai_regime_predictor(df):

    recent = df.iloc[-10:]

    adx_slope = recent["adx"].iloc[-1] - recent["adx"].iloc[0]
    atr_slope = recent["atr"].iloc[-1] - recent["atr"].iloc[0]
    ema_slope = recent["ema20"].iloc[-1] - recent["ema20"].iloc[0]

    vol_delta = (
        recent["volume"].mean()
        - df["volume"].rolling(50).mean().iloc[-1]
    )

    score = 0

    if adx_slope > 0:
        score += 0.25

    if atr_slope > 0:
        score += 0.25

    if abs(ema_slope) > recent["atr"].iloc[-1]:
        score += 0.25

    if vol_delta > 0:
        score += 0.25

    if score >= 0.75:
        regime = "EXPANSION"
    elif score >= 0.5:
        regime = "TREND"
    elif score >= 0.25:
        regime = "NEUTRAL"
    else:
        regime = "COMPRESSION"

    return regime, score
# ================= VOLATILITY TARGET ENGINE =================

import numpy as np

TARGET_VOL = 0.20   # yıllık hedef %20
MAX_RISK = 0.01     # üst sınır %1
MIN_RISK = 0.002    # alt sınır %0.2

def annualized_volatility(df):

    returns = df["close"].pct_change().dropna()

    if len(returns) < 30:
        return None

    daily_vol = np.std(returns)

    annual_vol = daily_vol * np.sqrt(365)

    return annual_vol


def volatility_adjusted_risk(df, base_risk):

    vol = annualized_volatility(df)

    if vol is None or vol == 0:
        return base_risk

    adjusted = base_risk * (TARGET_VOL / vol)

    if adjusted > MAX_RISK:
        adjusted = MAX_RISK

    if adjusted < MIN_RISK:
        adjusted = MIN_RISK

    return adjusted
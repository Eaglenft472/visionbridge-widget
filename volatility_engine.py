# ================= VOLATILITY ENGINE =================

import numpy as np

def volatility_metrics(df):

    atr_series = df["atr"].dropna()

    if len(atr_series) < 50:
        return None

    current_atr = atr_series.iloc[-1]

    percentile = (
        np.sum(atr_series < current_atr) / len(atr_series)
    )

    atr_mean = np.mean(atr_series[-30:])
    atr_std = np.std(atr_series[-30:])

    compression = current_atr < (atr_mean - atr_std * 0.7)
    expansion = current_atr > (atr_mean + atr_std * 0.7)

    return {
        "percentile": percentile,
        "compression": compression,
        "expansion": expansion
    }
# ================= STATISTICAL CORE ENGINE =================

import numpy as np
from performance_engine import load_logs

LOOKBACK = 50

def rolling_stats():

    logs = load_logs()

    if len(logs) < LOOKBACK:
        return None

    last = logs[-LOOKBACK:]

    R_values = np.array([x["R"] for x in last])

    mean_R = np.mean(R_values)
    std_R = np.std(R_values)

    # Sharpe approximation (trade-based)
    sharpe = mean_R / std_R if std_R != 0 else 0

    winrate = len(R_values[R_values > 0]) / len(R_values)

    expectancy = mean_R

    # Skewness
    skew = (
        np.mean((R_values - mean_R) ** 3) /
        (std_R ** 3) if std_R != 0 else 0
    )

    return {
        "sharpe": sharpe,
        "winrate": winrate,
        "expectancy": expectancy,
        "skew": skew
    }
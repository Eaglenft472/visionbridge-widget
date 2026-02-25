# ================= EDGE VALIDATION ENGINE v2 =================

import numpy as np
from performance_engine import load_logs

LOOKBACK = 30

def edge_metrics():
    logs = load_logs()

    if not logs or len(logs) < 10:  # 30 beklemiyoruz artık
        return None

    last = logs[-LOOKBACK:]

    R_values = [x.get("R", 0) for x in last if "R" in x]

    if not R_values:
        return None

    winrate = len([x for x in R_values if x > 0]) / len(R_values)

    avg_win = np.mean([x for x in R_values if x > 0]) if any(x > 0 for x in R_values) else 0
    avg_loss = abs(np.mean([x for x in R_values if x <= 0])) if any(x <= 0 for x in R_values) else 0

    expectancy = (winrate * avg_win) - ((1 - winrate) * avg_loss)

    return {
        "winrate": winrate,
        "expectancy": expectancy
    }


def mode_switch():

    metrics = edge_metrics()

    # İlk aşama: Henüz yeterli veri yoksa sistemi kilitleme
    if not metrics:
        return "WARMUP", 0.70, 1.0   # <-- ÖNEMLİ DEĞİŞİKLİK

    winrate = metrics["winrate"]
    expectancy = metrics["expectancy"]

    # DEFENSIVE MODE
    if winrate < 0.45 or expectancy < 0:
        return "DEFENSIVE", 0.80, 0.8

    # AGGRESSIVE MODE
    if winrate > 0.60 and expectancy > 0.3:
        return "AGGRESSIVE", 0.65, 1.2

    # NORMAL MODE
    return "NORMAL", 0.70, 1.0
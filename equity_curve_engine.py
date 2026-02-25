# ================= EQUITY CURVE ENGINE =================

def generate_equity_ascii(logs, width=40):

    if not logs:
        return "No Data"

    equities = [t.get("equity") for t in logs if t.get("equity")]

    if len(equities) < 2:
        return "Insufficient Data"

    min_eq = min(equities)
    max_eq = max(equities)

    if max_eq - min_eq == 0:
        return "Flat"

    normalized = [
        int((eq - min_eq) / (max_eq - min_eq) * (width - 1))
        for eq in equities
    ]

    chart = ""

    for value in normalized[-20:]:
        chart += "▇" * (value + 1) + "\n"

    return chart
# ================= EQUITY CURVE ENGINE v2 =================

import numpy as np

def generate_equity_ascii(logs, width=30):

    if not logs:
        return "No trades yet"

    equities = [t.get("equity") for t in logs if t.get("equity")]

    if len(equities) < 5:
        return "Collecting data..."

    last_values = equities[-20:]

    min_eq = min(last_values)
    max_eq = max(last_values)

    if max_eq - min_eq == 0:
        return "Flat equity"

    bars = []

    for eq in last_values:
        norm = (eq - min_eq) / (max_eq - min_eq)
        bar_height = int(norm * width)
        bars.append("▇" * bar_height)

    trend = np.polyfit(range(len(last_values)), last_values, 1)[0]

    trend_symbol = "📈" if trend > 0 else "📉"

    return "\n".join(bars) + f"\nTrend: {trend_symbol}"
# ================= CAPITAL SCALING ENGINE =================

import math

BASE_EQUITY_REFERENCE = 100  # başlangıç referans
MAX_SCALING_MULTIPLIER = 2.0
MIN_SCALING_MULTIPLIER = 0.5

def capital_scaled_risk(equity, peak, base_risk):

    if equity <= 0:
        return base_risk

    # Logarithmic growth scaling
    scale = math.log((equity / BASE_EQUITY_REFERENCE) + 1)

    if scale < 1:
        scale = 1

    if scale > MAX_SCALING_MULTIPLIER:
        scale = MAX_SCALING_MULTIPLIER

    # Peak dampener
    peak_factor = equity / peak if peak else 1

    if peak_factor < 1:
        scale *= peak_factor

    final_risk = base_risk * scale

    # Clamp
    if final_risk < base_risk * MIN_SCALING_MULTIPLIER:
        final_risk = base_risk * MIN_SCALING_MULTIPLIER

    if final_risk > base_risk * MAX_SCALING_MULTIPLIER:
        final_risk = base_risk * MAX_SCALING_MULTIPLIER

    return final_risk
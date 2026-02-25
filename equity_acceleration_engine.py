# ================= EQUITY ACCELERATION ENGINE =================

def aggressive_risk_boost(base_risk, logs, equity, peak):

    if not logs or len(logs) < 5:
        return base_risk

    last_trades = logs[-5:]
    wins = [t for t in last_trades if t.get("R", 0) > 0]

    win_rate = len(wins) / len(last_trades)

    # Equity momentum
    equity_growth = (equity - peak * 0.95) / peak if peak > 0 else 0

    boost = 1.0

    # If win rate strong, boost
    if win_rate >= 0.6:
        boost *= 1.15

    # If equity near peak and growing
    if equity_growth > 0:
        boost *= 1.1

    # Cap boost
    if boost > 1.3:
        boost = 1.3

    return base_risk * boost
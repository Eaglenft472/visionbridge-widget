# ================= PERFORMANCE ANALYTICS ENGINE =================

def calculate_performance_metrics(logs):

    if not logs or len(logs) < 5:
        return None

    r_values = [t.get("R", 0) for t in logs]

    total = len(r_values)
    wins = [r for r in r_values if r > 0]
    losses = [r for r in r_values if r < 0]

    win_rate = len(wins) / total if total > 0 else 0
    avg_r = sum(r_values) / total if total > 0 else 0

    avg_win = sum(wins) / len(wins) if wins else 0
    avg_loss = abs(sum(losses) / len(losses)) if losses else 0

    profit_factor = (
        (sum(wins) / abs(sum(losses)))
        if losses and sum(losses) != 0
        else 0
    )

    expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)

    # max consecutive loss
    max_consec_loss = 0
    current_loss = 0
    for r in r_values:
        if r < 0:
            current_loss += 1
            max_consec_loss = max(max_consec_loss, current_loss)
        else:
            current_loss = 0

    return {
        "total_trades": total,
        "win_rate": round(win_rate * 100, 2),
        "avg_r": round(avg_r, 3),
        "expectancy": round(expectancy, 3),
        "profit_factor": round(profit_factor, 2),
        "max_consec_loss": max_consec_loss
    }
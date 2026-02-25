import json
import os

LOG_FILE = "trade_log.json"


def load_logs():
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, "r") as f:
        return json.load(f)


def save_log(data):
    logs = load_logs()
    logs.append(data)
    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=4)


# =========================
# PERFORMANCE METRICS
# =========================

def compute_stats():
    logs = load_logs()
    if not logs:
        return {
            "total": 0,
            "winrate": 0,
            "avg_R": 0,
            "equity_curve": []
        }

    total = len(logs)
    wins = [t for t in logs if t["R"] > 0]
    winrate = len(wins) / total if total > 0 else 0
    avg_R = sum(t["R"] for t in logs) / total

    equity = 0
    equity_curve = []
    for t in logs:
        equity += t["R"]
        equity_curve.append(equity)

    return {
        "total": total,
        "winrate": winrate,
        "avg_R": avg_R,
        "equity_curve": equity_curve
    }


def loss_streak():
    logs = load_logs()
    streak = 0
    max_streak = 0

    for t in logs:
        if t["R"] < 0:
            streak += 1
            max_streak = max(max_streak, streak)
        else:
            streak = 0

    return max_streak
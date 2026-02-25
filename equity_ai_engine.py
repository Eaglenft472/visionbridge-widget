import json
import os

LOG_FILE = "trade_log.json"

def load_logs():
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, "r") as f:
        return json.load(f)

def equity_metrics():
    logs = load_logs()

    if len(logs) < 5:
        return None

    equity = 0
    curve = []

    for t in logs:
        equity += t.get("R", 0)
        curve.append(equity)

    slope = curve[-1] - curve[0]
    momentum = curve[-1] - curve[-3]

    return {
        "slope": slope,
        "momentum": momentum
    }
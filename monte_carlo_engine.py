import random

def monte_carlo_analysis(logs, simulations=500):

    if not logs or len(logs) < 5:
        return None

    returns = [t.get("R", 0) for t in logs]

    results = []

    for _ in range(simulations):
        equity = 0
        sampled = random.choices(returns, k=len(returns))

        for r in sampled:
            equity += r

        results.append(equity)

    results.sort()

    worst_case = results[int(len(results) * 0.05)]
    best_case = results[int(len(results) * 0.95)]
    median = results[int(len(results) * 0.5)]

    return {
        "worst_5pct": worst_case,
        "median": median,
        "best_95pct": best_case
    }
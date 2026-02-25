import statistics

def rolling_stats(values):
    if len(values) < 5:
        return None

    mean = statistics.mean(values)
    std = statistics.stdev(values)

    return {
        "mean": mean,
        "std": std
    }
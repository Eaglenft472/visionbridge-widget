def adaptive_aggression(risk, score, stats, mc):

    boost = 1.0

    # Yüksek skor boost
    if score > 0.9:
        boost += 0.25

    # Winning streak boost
    if stats and stats.get("win_rate", 0) > 0.6:
        boost += 0.20

    # Monte Carlo güçlü ise
    if mc and mc.get("worst_5pct", 0) > -0.15:
        boost += 0.15

    # Negatif expectancy savunma
    if stats and stats.get("expectancy", 0) < 0:
        boost -= 0.30

    return max(risk * boost, 0)
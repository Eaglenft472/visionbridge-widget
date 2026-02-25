# ================= ADAPTIVE RISK ENGINE v4 (STABLE) =================

from config import BASE_RISK
from performance_engine import compute_stats, loss_streak
from equity_ai_engine import equity_metrics
from volatility_engine import volatility_metrics

# Risk sınırları
MAX_RISK = BASE_RISK
MIN_RISK = BASE_RISK * 0.4


def dynamic_risk(equity, peak, df=None):
    """
    Enterprise Hybrid Risk Engine (Stable Version)
    """

    base = BASE_RISK

    # =========================
    # 1. DRAWDOWN CONTROL
    # =========================
    dd = (peak - equity) / peak if peak and peak > 0 else 0

    if dd > 0.10:
        base *= 0.5
    elif dd > 0.06:
        base *= 0.7

    # =========================
    # 2. VOLATILITY RADAR
    # =========================
    if df is not None:
        v_stats = volatility_metrics(df)

        if isinstance(v_stats, dict):

            if v_stats.get("compression"):
                base *= 1.10

            if v_stats.get("expansion") or \
               (isinstance(v_stats.get("percentile"), (int, float)) and v_stats.get("percentile") > 0.85):
                base *= 0.80

    # =========================
    # 3. EQUITY AI FILTER
    # =========================
    metrics = equity_metrics()

    if isinstance(metrics, dict):

        slope = metrics.get("slope")
        momentum = metrics.get("momentum")
        winrate_ai = metrics.get("winrate")
        volatility = metrics.get("volatility")

        if isinstance(slope, (int, float)) and slope < 0:
            base *= 0.6

        if isinstance(momentum, (int, float)) and momentum < 0:
            base *= 0.7

        if isinstance(winrate_ai, (int, float)) and winrate_ai < 0.5:
            base *= 0.7

        if isinstance(volatility, (int, float)) and volatility > 5:
            base *= 0.8

    # =========================
    # 4. PERFORMANCE BOOST
    # =========================
    stats = compute_stats()

    if isinstance(stats, dict):

        winrate = stats.get("winrate")

        if isinstance(winrate, (int, float)):

            if winrate > 0.65:
                base *= 1.15

            elif winrate < 0.40:
                base *= 0.6

    # =========================
    # 5. LOSS STREAK PROTECTION
    # =========================
    streak = loss_streak()

    if isinstance(streak, int):

        if streak >= 3:
            base *= 0.6

        if streak >= 5:
            print(f"🛑 CIRCUIT BREAKER: {streak} loss streak.")
            return 0

    # =========================
    # 6. FINAL LIMITS
    # =========================
    base = max(MIN_RISK, min(base, MAX_RISK))

    return round(base, 5)
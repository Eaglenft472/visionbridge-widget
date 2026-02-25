# ================= PORTFOLIO RISK ENGINE =================

import numpy as np

MAX_PORTFOLIO_RISK = 0.02      # Toplam risk equity'nin %2’sini geçemez
CORRELATION_THRESHOLD = 0.75   # Korelasyon üstü risk çakışır
MAX_SYMBOL_EXPOSURE = 0.015    # Tek sembol max %1.5

def calculate_portfolio_risk(open_positions, equity):

    total_risk = 0

    for pos in open_positions:
        total_risk += pos["risk_amount"]

    return total_risk / equity


def correlation_matrix(dataframes):

    returns = []

    for df in dataframes:
        returns.append(df["close"].pct_change().dropna())

    min_len = min(len(r) for r in returns)
    aligned = [r[-min_len:] for r in returns]

    matrix = np.corrcoef(aligned)

    return matrix


def allow_new_trade(open_positions, new_risk_amount, equity):

    current_risk = calculate_portfolio_risk(open_positions, equity)

    if current_risk + (new_risk_amount / equity) > MAX_PORTFOLIO_RISK:
        return False

    if (new_risk_amount / equity) > MAX_SYMBOL_EXPOSURE:
        return False

    return True
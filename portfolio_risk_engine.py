# ================= PORTFOLIO RISK CAP ENGINE =================

MAX_PORTFOLIO_RISK = 0.06

def calculate_total_portfolio_risk(open_positions):
    """Tüm açık pozisyonların risk tutarını topla"""
    total_risk = 0.0
    for pos in open_positions:
        risk_amount = abs(float(pos.get("initialMargin", 0)))
        total_risk += risk_amount
    return total_risk

def can_open_new_trade(open_positions, equity, new_risk_amount):
    """Yeni trade açılabilir mi?"""
    total_current_risk = calculate_total_portfolio_risk(open_positions)
    total_after_new = total_current_risk + new_risk_amount
    max_allowed_risk = equity * MAX_PORTFOLIO_RISK
    
    if total_after_new > max_allowed_risk:
        print(f"🔴 PORTFOLIO CAP EXCEEDED: {total_after_new:.2f} > {max_allowed_risk:.2f}")
        return False
    else:
        print(f"✅ Portfolio risk OK: {total_after_new:.2f} / {max_allowed_risk:.2f}")
        return True

def get_portfolio_risk_utilization(open_positions, equity):
    """Risk yüzdesini döndür"""
    total_risk = calculate_total_portfolio_risk(open_positions)
    max_risk = equity * MAX_PORTFOLIO_RISK
    return (total_risk / max_risk) * 100 if max_risk > 0 else 0
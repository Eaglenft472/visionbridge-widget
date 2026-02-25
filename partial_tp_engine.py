# ================= PARTIAL TP ENGINE =================

def manage_partial_tp(binance, symbol, direction, entry, price, amount, R, state):
    """
    Partial Take Profit Logic
    TP1: 1R → %40 kapat
    TP2: 2R → %30 kapat
    Kalan %30 runner
    """

    # Güvenlik kontrolleri
    if not R or R == 0:
        return state

    if not amount or float(amount) == 0:
        return state

    pnl_R = (
        (price - entry) / R
        if direction == "LONG"
        else (entry - price) / R
    )

    try:

        # ================= TP1 =================
        if pnl_R >= 1 and not state.get("tp1_done", False):

            close_qty = abs(float(amount)) * 0.4

            binance.create_order(
                symbol,
                type="MARKET",
                side="SELL" if direction == "LONG" else "BUY",
                amount=close_qty,
                params={"reduceOnly": True}
            )

            state["tp1_done"] = True

        # ================= TP2 =================
        if pnl_R >= 2 and not state.get("tp2_done", False):

            close_qty = abs(float(amount)) * 0.3

            binance.create_order(
                symbol,
                type="MARKET",
                side="SELL" if direction == "LONG" else "BUY",
                amount=close_qty,
                params={"reduceOnly": True}
            )

            state["tp2_done"] = True

    except Exception as e:
        print("Partial TP Error:", e)

    return state
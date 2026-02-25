# ================= OPERATIONAL REDUNDANCY PRO =================

import time

HEARTBEAT_INTERVAL = 300   # 5 dakika
last_heartbeat = time.time()

def heartbeat():
    global last_heartbeat
    if time.time() - last_heartbeat > HEARTBEAT_INTERVAL:
        print("💓 ENGINE HEARTBEAT OK")
        last_heartbeat = time.time()


def orphan_position_check(binance, state):

    positions = binance.fetch_positions()
    active = False

    for p in positions:
        if float(p["contracts"]) != 0:
            active = True

    # Eğer pozisyon var ama state boşsa
    if active and state.get("entry") is None:
        print("⚠ ORPHAN POSITION DETECTED")
        return True

    return False


def ensure_stop_exists(binance, symbol, direction, amount, sl):

    orders = binance.fetch_open_orders(symbol)

    has_stop = False
    for o in orders:
        if "STOP" in o["type"].upper():
            has_stop = True
            break

    if not has_stop:
        print("⚠ STOP MISSING – RECREATING")

        side = "SELL" if direction == "LONG" else "BUY"

        binance.create_order(
            symbol,
            "STOP_MARKET",
            side,
            abs(amount),
            params={
                "stopPrice": float(binance.price_to_precision(symbol, sl)),
                "reduceOnly": True,
                "workingType": "MARK_PRICE"
            }
        )
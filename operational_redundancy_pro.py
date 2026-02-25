import time

def heartbeat():
    return True

def orphan_position_check(binance):
    try:
        positions = binance.fetch_positions()
        return positions
    except:
        return None

def ensure_stop_exists(binance, symbol):
    try:
        orders = binance.fetch_open_orders(symbol)
        stops = [o for o in orders if "STOP" in o["type"].upper()]
        return len(stops) > 0
    except:
        return False
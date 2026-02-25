import time

# ==========================================================
# SAFE MARKET ORDER (Hata Toleranslı Emir)
# ==========================================================
def safe_market_order(binance, symbol, direction, amount, retries=3):
    side = "buy" if direction == "LONG" else "sell"
    for attempt in range(retries):
        try:
            if side == "buy":
                order = binance.create_market_buy_order(symbol, amount)
            else:
                order = binance.create_market_sell_order(symbol, amount)

            print(f"✅ MARKET ORDER SUCCESS: {symbol} {direction}")
            return order
        except Exception as e:
            print(f"⚠ Order attempt {attempt+1} failed:", e)
            time.sleep(1)
    
    print("❌ MARKET ORDER FAILED COMPLETELY")
    return None

# ==========================================================
# ENSURE STOP EXISTS (Stop Emri Doğrulama)
# ==========================================================
def ensure_stop(binance, symbol, direction, amount, sl, create_stop_func):
    try:
        orders = binance.fetch_open_orders(symbol)
        stop_exists = False

        for o in orders:
            if "STOP" in o["type"].upper():
                stop_exists = True
                break

        if not stop_exists:
            print("⚠ STOP MISSING — RECREATING")
            create_stop_func(symbol, direction, amount, sl)
        else:
            # İşlem hızını yormamak için sessizce doğrulanır
            pass
    except Exception as e:
        print("Stop check error:", e)

# ==========================================================
# ORPHAN POSITION CHECK (Çift Yönlü Senkronizasyon)
# ==========================================================
def orphan_position_check(binance, state):
    """
    Borsa ve Bot hafızası (state) arasındaki uyumu denetler.
    Artık state parametresini kabul eder, TypeError vermez.
    """
    try:
        positions = binance.fetch_positions()
        # Sadece kontratı 0 olmayan aktif pozisyonlar
        active_positions = [p for p in positions if float(p.get("contracts", 0)) != 0]

        # SENARYO 1: Borsada işlem var ama bot 'boşta' sanıyor
        if active_positions and state.get("entry") is None:
            print("⚠ ORPHAN POSITION DETECTED: Exchange active, state empty.")
            return True

        # SENARYO 2: Bot 'işlemdeyim' diyor ama borsa boş (Stop patlamış olabilir)
        if not active_positions and state.get("entry") is not None:
            print("⚠ STATE DESYNC DETECTED: State filled, exchange empty.")
            return True

    except Exception as e:
        print("Orphan Check Error:", e)

    return False
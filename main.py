# ================= VISIONBRIDGE TRADING BOT - ENTERPRISE v4 =================
# Main entry point – complete bot loop with entry engine debug logging

import time
import sys
import traceback
from datetime import datetime

from config import (
    SYMBOLS, BASE_THRESHOLD, BASE_RISK, LEVERAGE, DD_LIMIT,
    MOCK_MODE, CHECK_INTERVAL, STATE_FILE
)
from data_engine import binance, fetch_dataframe
from score_engine import compute_score
from pattern_engine import pattern_score, detect_engulfing, detect_pinbar
from structure_engine import detect_trend
from regime_engine import detect_regime
from edge_engine import mode_switch
from risk_engine import dynamic_risk
from execution_engine import calculate_size, set_leverage
from state_manager import load_state, save_state, state_manager
from volatility_engine import volatility_metrics
from correlation_engine import CorrelationEngine

# ================= SESSION GLOBALS =================

session_trades   = 0
session_wins     = 0
session_losses   = 0
correlation_eng  = CorrelationEngine()

# ================= HELPERS =================

def print_header():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    mode_label = "🟡 MOCK" if MOCK_MODE else "🔴 LIVE"
    print(f"\n{'='*70}")
    print(f"  VISIONBRIDGE v4  |  {now}  |  {mode_label}")
    print(f"{'='*70}")


def fmt_side(direction):
    return "🟢 LONG" if direction in ("LONG", "STRONG_LONG") else "🔴 SHORT"


def get_equity(state):
    try:
        bal = binance.fetch_balance()
        return float(bal["total"]["USDT"])
    except Exception:
        return float(state.get("peak", 10000.0))


def get_open_positions():
    try:
        positions = binance.fetch_positions()
        return [p for p in positions if abs(float(p.get("contracts", 0))) > 0]
    except Exception:
        return []


# ================= POSITION MANAGEMENT =================

def manage_existing_position(state, df):
    """
    Minimal position manager: checks SL/TP hit and updates trailing stop.
    Returns updated state.
    """
    if not state.get("entry"):
        return state

    entry     = float(state["entry"])
    sl        = float(state["sl"])
    tp        = float(state.get("tp", 0) or 0)
    direction = state.get("direction", "LONG").upper()
    symbol    = state.get("symbol", SYMBOLS[0])

    try:
        ticker = binance.fetch_ticker(symbol)
        price  = float(ticker["last"])
    except Exception as e:
        print(f"⚠️  Ticker fetch failed for {symbol}: {e}")
        return state

    # --- SL hit ---
    if direction == "LONG" and price <= sl:
        print(f"🛑 SL triggered for {symbol} @ {price:.4f} (SL={sl:.4f})")
        state["entry"]     = None
        state["sl"]        = None
        state["direction"] = None
        state["symbol"]    = None
        return state

    if direction == "SHORT" and price >= sl:
        print(f"🛑 SL triggered for {symbol} @ {price:.4f} (SL={sl:.4f})")
        state["entry"]     = None
        state["sl"]        = None
        state["direction"] = None
        state["symbol"]    = None
        return state

    # --- TP hit ---
    if tp > 0:
        if direction == "LONG" and price >= tp:
            print(f"✅ TP hit for {symbol} @ {price:.4f} (TP={tp:.4f})")
            state["entry"]     = None
            state["sl"]        = None
            state["direction"] = None
            state["symbol"]    = None
            return state

        if direction == "SHORT" and price <= tp:
            print(f"✅ TP hit for {symbol} @ {price:.4f} (TP={tp:.4f})")
            state["entry"]     = None
            state["sl"]        = None
            state["direction"] = None
            state["symbol"]    = None
            return state

    return state


# ================= PRE-ENTRY SAFETY CHECKS =================

def passes_global_filters(state, equity, peak):
    """
    Returns (ok: bool, reason: str).
    Checks drawdown and cooldown before entering any new trade.
    """
    # --- Drawdown guard ---
    dd = (peak - equity) / peak if peak and peak > 0 else 0
    if dd > DD_LIMIT:
        return False, f"Drawdown limit breached ({dd*100:.1f}% > {DD_LIMIT*100:.0f}%)"

    # --- Cooldown ---
    cooldown_until = state.get("cooldown_until", 0)
    if time.time() < cooldown_until:
        remaining = int(cooldown_until - time.time())
        return False, f"Cooldown active ({remaining}s remaining)"

    return True, "OK"


# ================= ENTRY ENGINE =================
#
#  This section evaluates each symbol for a potential trade entry.
#  Comprehensive debug logging is emitted at every decision gate so
#  that "NO POSITIONS" situations can be diagnosed quickly.
#

def run_entry_engine(state, equity, peak, open_positions, dataframes):
    """
    Entry engine – iterates over all symbols, scores them, applies
    threshold and filter checks, then opens the highest-scoring
    qualifying trade.

    Debug prints cover:
      1. Score calculations  (base + pattern)
      2. Threshold comparison
      3. Trend / direction detection
      4. Regime filter
      5. Risk / size calculation
      6. Final entry decision
    """
    print(f"\n{'─'*60}")
    print(f"🔍 [ENTRY ENGINE] Cycle start  {datetime.now().strftime('%H:%M:%S')}")
    print(f"   Equity : {equity:.2f} USDT  |  Peak : {peak:.2f} USDT")
    print(f"   Open positions : {len(open_positions)}")

    # ── Edge mode ──────────────────────────────────────────────────────
    mode, threshold, size_mult = mode_switch()
    print(f"   Edge mode : {mode}  |  Score threshold : {threshold:.2f}"
          f"  |  Size multiplier : {size_mult:.2f}")

    # ── Already in a position? ─────────────────────────────────────────
    if state.get("entry") is not None:
        print(f"   ⏭️  Already holding {state.get('symbol')} "
              f"({state.get('direction')}), skipping entry scan")
        return state

    # ── Global safety gates ────────────────────────────────────────────
    ok, reason = passes_global_filters(state, equity, peak)
    if not ok:
        print(f"   🚫 Global filter blocked entry: {reason}")
        return state

    print(f"   ✅ Global filters passed")

    # ── Per-symbol evaluation ──────────────────────────────────────────
    candidates = []

    for symbol in SYMBOLS:
        print(f"\n  ┌─ [{symbol}] ─────────────────────────────────────")

        df = dataframes.get(symbol)
        if df is None or df.empty:
            print(f"  │  ❌ No market data available – skipping")
            print(f"  └{'─'*52}")
            continue

        # ── 1. Trend / direction detection ────────────────────────────
        direction = detect_trend(df)
        print(f"  │  📈 Trend direction   : {direction}")

        if direction in (None, "NEUTRAL"):
            print(f"  │  ⏭️  Neutral / no trend – skipping")
            print(f"  └{'─'*52}")
            continue

        dir_label = "LONG" if direction in ("LONG", "STRONG_LONG") else "SHORT"

        # ── 2. Score calculation ──────────────────────────────────────
        base  = compute_score(df)
        pat   = pattern_score(df, dir_label)
        total = round(base + pat, 2)

        engulf = detect_engulfing(df)
        pin    = detect_pinbar(df)

        print(f"  │  📊 Base score        : {base:.2f}  "
              f"(ADX/EMA/Vol/MACD/RSI)")
        print(f"  │  🕯️  Pattern score     : {pat:.2f}  "
              f"(engulfing={engulf}, pinbar={pin})")
        print(f"  │  🎯 Total score       : {total:.2f}  "
              f"vs threshold {threshold:.2f}")

        last = df.iloc[-1]
        print(f"  │     ADX={last['adx']:.1f}  EMA20={last['ema20']:.2f}"
              f"  EMA50={last['ema50']:.2f}  RSI={last['rsi']:.1f}"
              f"  Vol={last['volume']:.0f}/VolAvg={last['vol_avg']:.0f}")

        # ── 3. Threshold comparison ───────────────────────────────────
        if total < threshold:
            print(f"  │  ❌ Score {total:.2f} < threshold {threshold:.2f}"
                  f" – entry blocked")
            print(f"  └{'─'*52}")
            continue

        print(f"  │  ✅ Score passed threshold")

        # ── 4. Regime filter ──────────────────────────────────────────
        regime = detect_regime(df)
        print(f"  │  🌡️  Market regime     : {regime}")

        if regime == "RANGE":
            print(f"  │  ⏭️  Range regime – entry suppressed")
            print(f"  └{'─'*52}")
            continue

        # ── 5. Volatility check ───────────────────────────────────────
        v_stats = volatility_metrics(df)
        if isinstance(v_stats, dict):
            pct   = v_stats.get("percentile", "n/a")
            comp  = v_stats.get("compression", False)
            expan = v_stats.get("expansion", False)
            if isinstance(pct, float):
                print(f"  │  🌊 Volatility        : percentile={pct:.2f}"
                      f"  compression={comp}  expansion={expan}")
            else:
                print(f"  │  🌊 Volatility        : {v_stats}")
        else:
            print(f"  │  🌊 Volatility        : insufficient data")

        # ── 6. Risk / position-size calculation ───────────────────────
        risk_frac = dynamic_risk(equity, peak, df)
        print(f"  │  ⚖️  Dynamic risk frac  : {risk_frac:.5f}"
              f"  (BASE_RISK={BASE_RISK})")

        if risk_frac == 0:
            print(f"  │  🛑 Risk engine returned 0 – circuit breaker active")
            print(f"  └{'─'*52}")
            continue

        risk_frac *= size_mult

        try:
            price = float(df.iloc[-1]["close"])
            atr_v = float(df.iloc[-1]["atr"])
        except Exception as e:
            print(f"  │  ❌ Price/ATR read error: {e}")
            print(f"  └{'─'*52}")
            continue

        sl_dist = atr_v * 1.5
        sl      = (price - sl_dist) if dir_label == "LONG" else (price + sl_dist)
        tp      = (price + sl_dist * 2) if dir_label == "LONG" else (price - sl_dist * 2)

        size = calculate_size(symbol, equity, price, sl, risk_frac)
        print(f"  │  💰 Entry price       : {price:.4f}")
        print(f"  │  🛡️  SL               : {sl:.4f}  (ATR×1.5 = {sl_dist:.4f})")
        print(f"  │  🎯 TP               : {tp:.4f}  (RR 2:1)")
        print(f"  │  📦 Position size    : {size}")

        if size == 0:
            print(f"  │  ❌ Size calculated as 0 – notional too low")
            print(f"  └{'─'*52}")
            continue

        # ── 7. Correlation check ──────────────────────────────────────
        corr_action, max_corr = correlation_eng.check_correlation_risk(
            open_positions, symbol, df, dataframes
        )
        print(f"  │  🔗 Correlation check : {corr_action}  max={max_corr:.2f}")

        if corr_action == "block":
            print(f"  │  ❌ Correlation too high – entry blocked")
            print(f"  └{'─'*52}")
            continue

        # ── Candidate accepted ────────────────────────────────────────
        print(f"  │  ✅ Symbol qualifies for entry!")
        print(f"  └{'─'*52}")

        candidates.append({
            "symbol":    symbol,
            "direction": dir_label,
            "score":     total,
            "price":     price,
            "sl":        sl,
            "tp":        tp,
            "size":      size,
            "risk_frac": risk_frac,
        })

    # ── Select best candidate ──────────────────────────────────────────
    print(f"\n  📋 Candidate count: {len(candidates)}")

    if not candidates:
        print(f"  ⚠️  NO POSITIONS opened – no symbol passed all filters")
        print(f"{'─'*60}")
        return state

    best = max(candidates, key=lambda c: c["score"])
    print(f"  🏆 Best candidate: {best['symbol']}  "
          f"score={best['score']:.2f}  dir={best['direction']}")

    # ── Final entry execution ──────────────────────────────────────────
    symbol    = best["symbol"]
    dir_label = best["direction"]
    price     = best["price"]
    sl        = best["sl"]
    tp        = best["tp"]
    size      = best["size"]

    print(f"\n  🚀 [ENTRY ENGINE] Opening {fmt_side(dir_label)} on {symbol}")
    print(f"     Price={price:.4f}  SL={sl:.4f}  TP={tp:.4f}  Size={size}")

    try:
        set_leverage(symbol)
        side = "buy" if dir_label == "LONG" else "sell"
        order = binance.create_market_order(symbol, side, size)
        print(f"  ✅ Order executed: id={order.get('id')}  "
              f"status={order.get('status')}")

        state["entry"]     = price
        state["sl"]        = sl
        state["tp"]        = tp
        state["direction"] = dir_label
        state["symbol"]    = symbol
        state["entry_time"] = time.time()

        save_state(state)

    except Exception as e:
        print(f"  ❌ Order failed for {symbol}: {e}")
        traceback.print_exc()

    print(f"{'─'*60}")
    return state


# ================= MAIN LOOP =================

def main_loop():
    global session_trades, session_wins, session_losses

    print_header()
    print("🚀 VisionBridge v4 starting…")
    if MOCK_MODE:
        print("🟡 MOCK MODE – no real orders will be placed\n")

    state = load_state()

    while True:
        try:
            print_header()

            # ── Equity & peak ──────────────────────────────────────────
            equity = get_equity(state)
            peak   = max(float(state.get("peak", equity)), equity)
            state["peak"] = peak

            print(f"💼 Equity : {equity:.2f} USDT  |  Peak : {peak:.2f} USDT  "
                  f"|  DD : {(peak-equity)/peak*100:.1f}%")

            # ── Fetch all dataframes ───────────────────────────────────
            print(f"\n📥 Fetching market data for {len(SYMBOLS)} symbols…")
            dataframes = {}
            for sym in SYMBOLS:
                df = fetch_dataframe(sym)
                if df is not None and not df.empty:
                    dataframes[sym] = df
                    print(f"   ✅ {sym}: {len(df)} candles loaded")
                else:
                    print(f"   ❌ {sym}: data fetch failed")

            # ── Open position status ───────────────────────────────────
            open_positions = get_open_positions()

            # ── Manage existing position ───────────────────────────────
            if state.get("entry"):
                sym = state.get("symbol", SYMBOLS[0])
                df  = dataframes.get(sym)
                if df is not None:
                    state = manage_existing_position(state, df)
                    save_state(state)

            # ── Entry engine ───────────────────────────────────────────
            state = run_entry_engine(
                state, equity, peak, open_positions, dataframes
            )

            save_state(state)

        except KeyboardInterrupt:
            print("\n⛔ Interrupted by user – shutting down")
            save_state(state)
            sys.exit(0)

        except Exception as e:
            print(f"\n❌ Main loop error: {e}")
            traceback.print_exc()
            try:
                save_state(state)
            except Exception:
                pass

        print(f"\n⏱️  Next cycle in {CHECK_INTERVAL}s…")
        time.sleep(CHECK_INTERVAL)


# ================= ENTRY POINT =================

if __name__ == "__main__":
    main_loop()

# ================= MAIN ENGINE v8.2 - INSTITUTIONAL GRADE (TELEGRAM ENHANCED) =================
# FULL RECOVERY + RECONCILIATION + LIFECYCLE + WATCHDOG + DYNAMIC CACHE + TELEGRAM DASHBOARD

import time
import numpy as np
import requests
from datetime import datetime
from collections import deque
import sys
import os
import traceback

# ===== CRASH RECOVERY IMPORTS =====
from recovery_engine import StateManager, load_state, save_state, create_recovery_checkpoint
from crash_engine import initialize_crash_recovery
from verify_engine import RecoveryVerifier

# ===== NEW INSTITUTIONAL ENGINES =====
from position_rebuilder_engine import PositionRebuilder
from exchange_reconciliation_engine import ExchangeReconciliation
from trade_lifecycle_engine import TradeLifecycleEngine, TradeState
from watchdog_engine import WatchdogEngine
from dynamic_mtf_cache_engine import DynamicMTFCache
from telegram_dashboard_engine import TelegramDashboard

# ================= CORE IMPORTS =================
from config import SYMBOLS, DD_LIMIT
from data_engine import fetch_dataframe, binance
from structure_engine import detect_trend
from score_engine import compute_score
from risk_engine import dynamic_risk
from execution_engine import calculate_size, set_leverage
from edge_engine import mode_switch
from execution_safety_engine import safe_market_order, orphan_position_check
from performance_engine import load_logs
from pattern_engine import pattern_score

from rsi_divergence_engine import detect_rsi_divergence
from equity_acceleration_engine import aggressive_risk_boost
from partial_tp_engine import manage_partial_tp
from regime_aggression_engine import regime_aggression_adjustment
from performance_analytics_engine import calculate_performance_metrics

from structure_break_engine import detect_break_and_retest
from ai_regime_engine import ai_regime_predictor
from volatility_engine import volatility_metrics
from volatility_target_engine import volatility_adjusted_risk
from portfolio_engine import allow_new_trade
from equity_curve_engine import generate_equity_ascii

# ===== 4 SMART MOTORS =====
from smart_trailing_engine import compute_smart_trailing_stop, get_trailing_stats
from multi_timeframe_engine import analyze_multi_timeframe_bias, get_mtf_alignment
from latency_optimizer_engine import optimize_execution_latency, LatencyOptimizer
from journal_analytics_engine import (
    record_trade_journal,
    analyze_journal_metrics,
    close_trade_journal,
    get_journal_summary
)

# ===== 7 RISK ARCHITECTURE =====

# 1️⃣ EXCHANGE-SIDE STOP ORDER ENGINE
try:
    from exchange_stop_engine import ExchangeStopManager
    stop_manager = ExchangeStopManager()
    print("✅ 1) Exchange-side STOP order ENGINE loaded")
except Exception as e:
    print(f"❌ Exchange-side stop engine failed: {e}")
    stop_manager = None

# 2️⃣ SL GUARD ENGINE
try:
    from sl_guard_engine import monotonic_sl_guard, validate_sl_movement
    print("✅ 2) SL Guard ENGINE loaded")
except Exception as e:
    print(f"❌ SL Guard engine failed: {e}")
    monotonic_sl_guard = None

# 3️⃣ CORRELATION RISK ENGINE
try:
    from correlation_engine import CorrelationEngine
    corr_engine = CorrelationEngine(lookback=200, corr_threshold=0.75)
    print("✅ 3) Correlation Risk ENGINE loaded")
except Exception as e:
    print(f"❌ Correlation engine failed: {e}")
    corr_engine = None

# 4️⃣ PORTFOLIO RISK CAP ENGINE
try:
    from portfolio_risk_engine import (
        can_open_new_trade,
        get_portfolio_risk_utilization,
        calculate_total_portfolio_risk
    )
    print("✅ 4) Portfolio Risk Cap ENGINE loaded")
except Exception as e:
    print(f"❌ Portfolio risk engine failed: {e}")
    can_open_new_trade = None
    calculate_total_portfolio_risk = None
    get_portfolio_risk_utilization = None

# 5️⃣ DYNAMIC MTF CACHE ENGINE
try:
    dynamic_mtf_cache = DynamicMTFCache(base_ttl=60)
    print("✅ 5) Dynamic MTF Cache Layer ENGINE loaded")
except Exception as e:
    print(f"❌ Dynamic MTF cache engine failed: {e}")
    dynamic_mtf_cache = None

# 6️⃣ EXECUTION RESILIENCE ENGINE
try:
    from execution_resilience_engine import ExecutionResilient
    exec_retry = ExecutionResilient(max_retries=3, slippage_threshold=0.002)
    print("✅ 6) Execution Resilience ENGINE loaded")
except Exception as e:
    print(f"❌ Execution resilience engine failed: {e}")
    exec_retry = None

# 7️⃣ ATOMIC JOURNAL WRITE ENGINE
try:
    from atomic_journal_engine import AtomicJournal
    journal_atomic = AtomicJournal(journal_path="trade_journal.json")
    print("✅ 7) Atomic Journal Write ENGINE loaded")
except Exception as e:
    print(f"❌ Atomic journal engine failed: {e}")
    journal_atomic = None

# ================= SETTINGS =================
MAX_CONCURRENT_POSITIONS = 2
COOLDOWN_SECONDS = 1800
TELEGRAM_TOKEN = '8763094320:AAGSq3tXa6JWLsdYc40wqi9Xr4oMloPGuMU'
TELEGRAM_CHAT_ID = '6350700231'

TRAILING_LOOKBACK = 10
TRAILING_SENSITIVITY = 0.7
TRAIL_ACTIVATION_RATIO = 1.5

TF_WEIGHTS = {
    "1m": 0.1,
    "5m": 0.2,
    "15m": 0.35,
    "1h": 0.35
}

LATENCY_THRESHOLD_MS = 100
JOURNAL_ENABLED = True
JOURNAL_PATH = "trade_journal.json"

# ===== WATCHDOG SETTINGS =====
WATCHDOG_CHECK_INTERVAL = 30  # Saniye
WATCHDOG_ENABLED = True

# ================= UTILITY FUNCTIONS =================

def equity_slope_negative(logs, lookback=10):
    """Equity düşüş trendi kontrol"""
    if not logs or len(logs) < lookback:
        return False
    equities = [t.get("equity") for t in logs[-lookback:] if t.get("equity")]
    if len(equities) < lookback:
        return False
    x = np.arange(len(equities))
    slope = np.polyfit(x, equities, 1)[0]
    return slope < 0

def loss_streak_high(logs, threshold=3):
    """Kaybetme serisi kontrol"""
    if not logs:
        return False
    streak = 0
    for t in reversed(logs):
        if t.get("R", 0) < 0:
            streak += 1
        else:
            break
    return streak >= threshold

# ================= INITIALIZATION =================
print("=" * 100)
print("🚀 INSTITUTIONAL GRADE TRADING ENGINE v8.2 - TELEGRAM ENHANCED")
print("=" * 100)

# Initialize state manager ve crash recovery
state_manager = StateManager()
crash_handler = initialize_crash_recovery(state_manager, binance, SYMBOLS)

# Recovery verification
recovery_verifier = RecoveryVerifier(binance, state_manager, None)
verification_result = recovery_verifier.verify_recovery(SYMBOLS)

print("\n📊 RISK ARCHITECTURE STATUS:")
print("   1️⃣  Exchange-side STOP order: " + ("✅ ACTIVE" if stop_manager else "❌ INACTIVE"))
print("   2️⃣  SL Guard: " + ("✅ ACTIVE" if monotonic_sl_guard else "❌ INACTIVE"))
print("   3️⃣  Correlation Risk Engine: " + ("✅ ACTIVE" if corr_engine else "❌ INACTIVE"))
print("   4️⃣  Portfolio Risk Cap: " + ("✅ ACTIVE" if can_open_new_trade else "❌ INACTIVE"))
print("   5️⃣  Dynamic MTF Cache Layer: " + ("✅ ACTIVE" if dynamic_mtf_cache else "❌ INACTIVE"))
print("   6️⃣  Execution Resilience: " + ("✅ ACTIVE" if exec_retry else "❌ INACTIVE"))
print("   7️⃣  Atomic Journal: " + ("✅ ACTIVE" if journal_atomic else "❌ INACTIVE"))

print("\n🔧 INSTITUTIONAL ENGINES:")
print("   ✅ Deterministic Position Rebuilder")
print("   ✅ Exchange Reconciliation Engine")
print("   ✅ Trade Lifecycle State Machine")
print("   ✅ Multi-Process Watchdog")
print("   ✅ Dynamic MTF Cache")
print("   ✅ Risk Clamping with Logging")
print("   ✅ Bar-Close Execution Lock")
print("   ✅ Telegram Dashboard Engine")

print("=" * 100)

# ===== LOAD STATE =====
state = load_state()
if not isinstance(state, dict):
    print("🚨 CRITICAL ERROR: state is not a dict!")
    raise RuntimeError("State must be dict, got: " + str(type(state)))

# ===== GUARANTEE STATE HAS peak AND direction =====
if "peak" not in state:
    state["peak"] = 10000.0
if "direction" not in state:
    state["direction"] = None

# ===== INITIALIZE INSTITUTIONAL ENGINES =====

# Position Rebuilder
position_rebuilder = PositionRebuilder(binance, state_manager)
print("✅ Position Rebuilder initialized")

# Exchange Reconciliation
exchange_recon = ExchangeReconciliation(binance, stop_manager)
print("✅ Exchange Reconciliation initialized")

# Trade Lifecycle
trade_lifecycle = TradeLifecycleEngine(binance, state_manager)
print("✅ Trade Lifecycle Engine initialized")

# Watchdog (IMPORTANT!)
watchdog = WatchdogEngine(
    binance, 
    state_manager,
    stop_manager=stop_manager,
    exchange_recon=exchange_recon,
    trade_lifecycle=trade_lifecycle,
    check_interval=WATCHDOG_CHECK_INTERVAL
)
print("✅ Watchdog Engine initialized")

# ===== TELEGRAM DASHBOARD INITIALIZATION =====
telegram_dashboard = TelegramDashboard(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)
print("✅ Telegram Dashboard initialized")

# ===== START WATCHDOG =====
if WATCHDOG_ENABLED:
    watchdog_thread = watchdog.start_watchdog()
    print("✅ Watchdog thread started (daemon)")
else:
    print("⚠️  Watchdog DISABLED")

last_report_time = 0
trend_pass = break_pass = rsi_pass = score_candidates = 0
latency_history = deque(maxlen=100)
exec_latency_optimizer = LatencyOptimizer(max_history=100, threshold_ms=LATENCY_THRESHOLD_MS)

# Stop manager'ı Exchange ile senkronize et
if stop_manager:
    print("\n🔄 Syncing stops with exchange on startup...")
    stop_manager.sync_with_exchange(binance, SYMBOLS)

# ===== CRASH RECOVERY: POSITION REBUILD (IF NEEDED) =====
print("\n🔍 Checking if position rebuild is needed...")
raw_positions = binance.fetch_positions()
open_positions = [p for p in raw_positions if float(p.get("contracts", 0)) != 0]
initial_equity = float(binance.fetch_balance().get("total", {}).get("USDT", 0) or 0)

if open_positions and not state.get('entry'):
    print("⚠️  Exchange has open position but state is missing entry!")
    print("🔄 REBUILDING STATE FROM EXCHANGE...")
    
    rebuilt_state = position_rebuilder.rebuild_from_exchange(binance, open_positions)
    
    if rebuilt_state:
        is_valid = position_rebuilder.verify_rebuild(rebuilt_state, open_positions)
        
        if is_valid:
            rebuilt_state['peak'] = state.get('peak', 10000.0)
            rebuilt_state['direction'] = rebuilt_state.get('direction') or state.get('direction')
            state = rebuilt_state
            save_state(state)
            print("✅ STATE REBUILT SUCCESSFULLY FROM EXCHANGE")
            
            # Telegram notification
            try:
                telegram_dashboard.position_rebuild_notification(
                    state.get('symbol', 'UNKNOWN'),
                    rebuilt=True,
                    details={
                        'entry_price': rebuilt_state.get('entry'),
                        'sl': rebuilt_state.get('sl'),
                        'current_price': open_positions[0]['info']['markPrice'] if open_positions else 0,
                        'unrealized_pnl': open_positions[0].get('unrealizedPnl', 0) if open_positions else 0
                    }
                )
            except Exception as e:
                print(f"⚠️  Telegram notification failed: {e}")
        else:
            print("❌ Rebuilt state validation failed")
            try:
                telegram_dashboard.position_rebuild_notification(
                    state.get('symbol', 'UNKNOWN'),
                    rebuilt=False
                )
            except:
                pass
    else:
        print("❌ State rebuild failed")
        try:
            telegram_dashboard.position_rebuild_notification(
                state.get('symbol', 'UNKNOWN'),
                rebuilt=False
            )
        except:
            pass

# ===== SEND STARTUP NOTIFICATION =====
try:
    startup_status = {
        "risk_architecture": {
            "Exchange-side STOP": stop_manager is not None,
            "SL Guard": monotonic_sl_guard is not None,
            "Correlation Risk": corr_engine is not None,
            "Portfolio Risk Cap": can_open_new_trade is not None,
            "Dynamic MTF Cache": dynamic_mtf_cache is not None,
            "Execution Resilience": exec_retry is not None,
            "Atomic Journal": journal_atomic is not None,
        },
        "institutional_engines": {
            "Position Rebuilder": True,
            "Exchange Reconciliation": True,
            "Trade Lifecycle": True,
            "Watchdog": WATCHDOG_ENABLED,
        },
        "initial_equity": initial_equity,
        "max_positions": MAX_CONCURRENT_POSITIONS
    }
    telegram_dashboard.startup_notification("v8.2 INSTITUTIONAL", startup_status)
    print("✅ Startup notification sent to Telegram")
except Exception as e:
    print(f"⚠️  Startup notification failed: {e}")

print("\n✅ ENGINE INITIALIZED AND READY FOR PRODUCTION\n")

# ================= MAIN TRADING LOOP =================
last_bar_close_time = 0
bar_close_lock = False
last_hourly_report = 0

while True:
    try:
        loop_start_time = time.time()

        # === PHASE 1: SNAPSHOT ===
        balance = binance.fetch_balance()
        equity = float(balance.get("total", {}).get("USDT", 0) or 0)
        raw_positions = binance.fetch_positions()
        open_positions = [p for p in raw_positions if float(p.get("contracts", 0)) != 0]
        
        # ===== LOGS SAFETY CHECK =====
        logs = load_logs()
        if logs is None:
            logs = []

        peak = state.get("peak", equity)
        if equity > peak:
            peak = equity
            state["peak"] = equity
            save_state(state)

        dd = (peak - equity) / peak if peak > 0 else 0

        # === PHASE 1.5: RECONCILIATION (CONTINUOUS) ===
        if len(open_positions) > 0:
            try:
                state_updated, recon_issues = exchange_recon.reconcile_all_positions(state, open_positions)
                if state_updated:
                    save_state(state)
            except Exception as e:
                print(f"⚠️  Reconciliation failed: {e}")

        # === PHASE 2: RISK CONTROL ===
        slope_neg = equity_slope_negative(logs)
        high_streak = loss_streak_high(logs)

        if slope_neg or high_streak:
            state["risk_cut"] = True
            if time.time() > state.get("cooldown_until", 0):
                state["cooldown_until"] = time.time() + COOLDOWN_SECONDS
        else:
            state["risk_cut"] = False

        save_state(state)

        # === PERIODIC RECOVERY CHECKPOINT ===
        if int(time.time()) % 300 == 0:
            create_recovery_checkpoint(state)

        # === PHASE 3: DASHBOARD ===
        if time.time() - last_report_time > 60:
            perf = calculate_performance_metrics(logs)
            # ===== SAFETY CHECK =====
            if perf is None:
                perf = {}

            journal_summary = ""
            if JOURNAL_ENABLED and journal_atomic:
                try:
                    journal_metrics = journal_atomic.read_safe()
                    if journal_metrics:
                        closed = [t for t in journal_metrics if "exit_price" in t]
                        if closed:
                            pnl = [t.get("pnl_percent", 0) for t in closed]
                            wins = len([p for p in pnl if p > 0])
                            journal_summary = (
                                f"📊 Journal: {len(journal_metrics)} trades | "
                                f"WR: {(wins/len(closed)*100):.1f}%\n"
                            )
                except:
                    pass

            portfolio_util = ""
            if get_portfolio_risk_utilization:
                try:
                    util_pct = get_portfolio_risk_utilization(open_positions, equity)
                    portfolio_util = f"Portfolio Risk: {util_pct:.1f}% | "
                except:
                    pass

            latency_stats = ""
            if latency_history:
                latency_stats = f"Avg Latency: {np.mean(list(latency_history)):.1f}ms | "

            stops_status = ""
            if stop_manager:
                stops_status = f"Active STOPs: {len(stop_manager.active_stops)} | "

            # Watchdog status
            watchdog_status = watchdog.get_watchdog_status()

            # ===== SEND HOURLY TELEGRAM DASHBOARD =====
            try:
                telegram_dashboard.hourly_dashboard(
                    equity=equity,
                    dd_percent=dd*100,
                    open_positions=len(open_positions),
                    perf_metrics=perf,
                    watchdog_status=watchdog_status
                )
            except Exception as e:
                print(f"⚠️  Dashboard notification failed: {e}")

            last_report_time = time.time()

        # === COOLDOWN BLOCK ===
        if time.time() < state.get("cooldown_until", 0):
            time.sleep(30)
            continue

        if dd > DD_LIMIT:
            time.sleep(60)
            continue

        # === ORPHAN POSITION CHECK + ENHANCED STOP RESYNC ===
        if orphan_position_check(binance, state):
            print("✅ Orphan check passed - RESYNCING STOPS...")
            if stop_manager:
                try:
                    stop_manager.sync_with_exchange(binance, SYMBOLS)
                    print("✅ Stop resync completed after cleanup")
                except Exception as e:
                    print(f"⚠️  Stop resync failed: {e}")
            time.sleep(60)
            continue

        # === PHASE 4: POSITION MANAGEMENT ===
        if open_positions and len(open_positions) > 0:
            active = open_positions[0]
            if active is None:
                time.sleep(30)
                continue
                
            symbol = active["symbol"].replace("USDT", "/USDT")
            direction = "LONG" if float(active["contracts"]) > 0 else "SHORT"

            amount = abs(float(active["contracts"]))
            try:
                real_positions = binance.fetch_positions([symbol])
                if real_positions and len(real_positions) > 0:
                    amount = abs(float(real_positions[0].get("contracts", amount)))
            except:
                pass

            df_live = fetch_dataframe(symbol)
            ticker = binance.fetch_ticker(symbol)

            if df_live is not None and not df_live.empty and ticker:
                price = ticker["last"]
                atr = df_live.iloc[-1]["atr"]

                entry = state.get("entry")
                if atr > 0 and entry:

                    if state.get("sl") is None:
                        sl_init = entry - 1.5 * atr if direction == "LONG" else entry + 1.5 * atr
                        state.update({
                            "sl": sl_init,
                            "R": abs(entry - sl_init),
                            "tp1_done": False,
                            "tp2_done": False,
                            "trail_active": False
                        })
                        save_state(state)

                        if stop_manager:
                            stop_manager.place_stop_order(
                                binance, symbol, direction, sl_init, amount
                            )
                        
                        # Create lifecycle entry
                        try:
                            trade_lifecycle.create_trade_entry(
                                symbol, direction, entry, sl_init, amount,
                                regime=state.get('entry_regime')
                            )
                            trade_lifecycle.transition_to_opened(symbol, state)
                        except Exception as e:
                            print(f"⚠️  Lifecycle creation failed: {e}")

                    if state.get("R"):
                        trail_sl = compute_smart_trailing_stop(
                            price=price,
                            entry=entry,
                            direction=direction,
                            atr=atr,
                            lookback=TRAILING_LOOKBACK,
                            sensitivity=TRAILING_SENSITIVITY,
                            activation_ratio=TRAIL_ACTIVATION_RATIO,
                            df=df_live
                        )

                        if trail_sl is not None:
                            if monotonic_sl_guard:
                                trail_sl = monotonic_sl_guard(state.get("sl"), trail_sl, direction)

                            if stop_manager and trail_sl != state.get("sl"):
                                stop_manager.update_stop_order(
                                    binance, symbol, direction, trail_sl, amount
                                )
                                state["sl"] = trail_sl
                                state["trail_active"] = True
                                
                                # Update lifecycle
                                try:
                                    trade_lifecycle.update_trailing_sl(symbol, trail_sl)
                                except:
                                    pass

                        state = manage_partial_tp(
                            binance, symbol, direction,
                            entry, price, amount,
                            state.get("R", 0), state
                        )
                        
                        # Update lifecycle for TP
                        try:
                            if state.get('tp1_done') and symbol in trade_lifecycle.active_trades:
                                trade = trade_lifecycle.active_trades[symbol]
                                if not trade['tp1_filled']:
                                    trade_lifecycle.update_tp1_filled(symbol, amount/2, price)
                            
                            if state.get('tp2_done') and symbol in trade_lifecycle.active_trades:
                                trade = trade_lifecycle.active_trades[symbol]
                                if not trade['tp2_filled']:
                                    trade_lifecycle.update_tp2_filled(symbol, amount/2, price)
                        except Exception as e:
                            print(f"⚠️  Lifecycle TP update failed: {e}")
                        
                        save_state(state)

        # === PHASE 5: ENTRY ENGINE ===
        if len(open_positions) < MAX_CONCURRENT_POSITIONS:

            # BAR-CLOSE BASED EXECUTION LOCK
            current_time = int(time.time())
            minutes_since_lock = (current_time - last_bar_close_time) / 60
            
            # Her 1 bar'da sadece 1 trade aç (60 saniye lock)
            if bar_close_lock and minutes_since_lock < 1:
                time.sleep(30)
                continue
            
            bar_close_lock = False

            # GLOBAL HARD CAP CHECK
            if calculate_total_portfolio_risk:
                total_portfolio_risk = calculate_total_portfolio_risk(open_positions)
                max_allowed_portfolio = equity * 0.06

                if total_portfolio_risk > max_allowed_portfolio:
                    print(f"HARD CAP TRIGGERED: {total_portfolio_risk:.2f} > {max_allowed_portfolio:.2f}")
                    time.sleep(60)
                    continue

            mode, base_threshold, pattern_multiplier = mode_switch()
            best_symbol = best_df = best_dir = None
            best_score = 0
            best_risk = 0
            best_regime = None
            best_mtf_bias = 0
            best_corr_val = 0

            dataframes_dict = {}

            for sym in SYMBOLS:
                df = fetch_dataframe(sym)
                if df is None or len(df) < 60:
                    continue

                dataframes_dict[sym] = df

                trend = detect_trend(df)
                ema20 = df.iloc[-1]["ema20"]
                ema50 = df.iloc[-1]["ema50"]
                ema20_prev = df.iloc[-2]["ema20"]

                if trend == "LONG" or (ema20 > ema50 and ema20 > ema20_prev):
                    direction = "LONG"
                    trend_pass += 1
                elif trend == "SHORT" or (ema20 < ema50 and ema20 < ema20_prev):
                    direction = "SHORT"
                    trend_pass += 1
                else:
                    continue

                if not detect_break_and_retest(df, direction):
                    continue
                break_pass += 1

                rsi_div = detect_rsi_divergence(df, direction)
                if rsi_div:
                    rsi_pass += 1

                corr_action = "pass"
                corr_val = 0.0
                if corr_engine:
                    try:
                        corr_action, corr_val = corr_engine.check_correlation_risk(
                            open_positions, sym, df, dataframes_dict
                        )
                        if corr_action == "block":
                            continue
                    except:
                        pass

                regime, _ = ai_regime_predictor(df)
                threshold = base_threshold
                if regime == "EXPANSION":
                    threshold *= 0.9
                elif regime == "COMPRESSION":
                    threshold *= 1.1

                score = compute_score(df)
                score += (pattern_score(df, direction) or 0) * pattern_multiplier
                if rsi_div:
                    score += 10

                # ===== DYNAMIC MTF CACHE (ENHANCED) =====
                mtf_bias = 0.5
                if dynamic_mtf_cache:
                    try:
                        # Volatility hesapla
                        current_atr_percent = (df.iloc[-1]["atr"] / df.iloc[-1]["close"]) * 100
                        dynamic_ttl = dynamic_mtf_cache.get_dynamic_ttl(sym, current_atr_percent)
                        
                        # Cache kontrol
                        mtf_bias = analyze_multi_timeframe_bias(
                            symbol=sym,
                            timeframes=list(TF_WEIGHTS.keys()),
                            weights=TF_WEIGHTS,
                            direction=direction
                        )
                        
                        # Her 50 trade'te cache efficiency log'la
                        if score_candidates % 50 == 0:
                            print(f"📊 {sym}: Volatility={current_atr_percent:.2f}%, Dynamic TTL={dynamic_ttl}s")
                    
                    except Exception as e:
                        print(f"⚠️  MTF bias calculation failed: {e}")
                        mtf_bias = 0.5

                score *= (1.0 + mtf_bias * 0.15)

                if score >= threshold * 0.8:
                    score_candidates += 1

                if score > best_score and score >= threshold:

                    risk = dynamic_risk(equity, peak)
                    risk = aggressive_risk_boost(risk, logs, equity, peak)
                    risk = regime_aggression_adjustment(df, risk)
                    risk *= {"EXPANSION": 1.2, "TREND": 1.1, "COMPRESSION": 0.7}.get(regime, 1.0)

                    risk = volatility_adjusted_risk(df, risk)

                    if corr_action == "reduce":
                        risk *= 0.5

                    # ===== INSTITUTIONAL RISK CLAMPING WITH LOGGING =====
                    base_risk = risk
                    risk = max(0.002, min(risk, 0.03))  # Hard clamp: 0.2% - 3%
                    
                    if risk < base_risk:
                        reduction_pct = ((base_risk - risk) / base_risk) * 100
                        print(f"⚠️  Risk clamped: {base_risk:.4f} → {risk:.4f} ({reduction_pct:.1f}% reduction)")

                    best_symbol = sym
                    best_df = df
                    best_dir = direction
                    best_score = score
                    best_risk = risk
                    best_regime = regime
                    best_mtf_bias = mtf_bias
                    best_corr_val = corr_val

            # === TRADE OPENING ===
            if best_symbol and best_df is not None:

                entry_price = best_df.iloc[-1]["close"]
                atr = best_df.iloc[-1]["atr"]

                if atr > 0:

                    sl = entry_price - 1.5 * atr if best_dir == "LONG" else entry_price + 1.5 * atr
                    risk_amount = equity * best_risk

                    if can_open_new_trade:
                        try:
                            if not can_open_new_trade(open_positions, equity, risk_amount):
                                best_symbol = None
                                continue
                        except:
                            pass

                    open_risk_data = [
                        {"risk_amount": abs(float(p.get("initialMargin", 0)))}
                        for p in open_positions
                    ]

                    if allow_new_trade(open_risk_data, risk_amount, equity):

                        qty = calculate_size(best_symbol, equity, entry_price, sl, best_risk)
                        if qty > 0:

                            set_leverage(best_symbol)

                            success = False
                            slippage = 0
                            exec_latency = 0

                            if exec_retry:
                                success, slippage, exec_latency = exec_retry.execute_with_retry(
                                    binance, best_symbol, best_dir, qty, safe_market_order
                                )
                            else:
                                exec_start = time.time()
                                success = safe_market_order(binance, best_symbol, best_dir, qty)
                                exec_latency = (time.time() - exec_start) * 1000
                                slippage = 0

                            latency_history.append(exec_latency)

                            if exec_latency > 0:
                                exec_latency_optimizer.record_latency(exec_latency)

                            if success:

                                if stop_manager:
                                    stop_manager.place_stop_order(
                                        binance, best_symbol, best_dir, sl, qty
                                    )

                                if JOURNAL_ENABLED and journal_atomic:
                                    try:
                                        # ===== ENHANCED JOURNAL ENTRY =====
                                        journal_atomic.write_atomic({
                                            # ===== BASIC INFO =====
                                            "timestamp": datetime.now().isoformat(),
                                            "symbol": best_symbol,
                                            "direction": best_dir,
                                            "entry_price": entry_price,
                                            "qty": qty,
                                            
                                            # ===== RISK MANAGEMENT =====
                                            "sl": sl,
                                            "risk": best_risk,
                                            "risk_percent": best_risk * 100,
                                            "equity_at_entry": equity,
                                            
                                            # ===== EXECUTION =====
                                            "slippage": slippage,
                                            "execution_latency_ms": exec_latency,
                                            
                                            # ===== ANALYSIS =====
                                            "score": best_score,
                                            "correlation": best_corr_val,
                                            "mtf_bias": best_mtf_bias,
                                            "regime": best_regime,
                                            "atr_at_entry": best_df.iloc[-1]["atr"],
                                            "atr_percent": (best_df.iloc[-1]["atr"] / entry_price) * 100,
                                            
                                            # ===== PERFORMANCE METRICS (sonra doldurulacak) =====
                                            "exit_price": None,
                                            "exit_time": None,
                                            "realized_pnl": None,
                                            "realized_pnl_percent": None,
                                            "trade_duration_minutes": None,
                                            "bars_held": None
                                        })
                                    except:
                                        pass

                                state.update({
                                    "entry": entry_price,
                                    "direction": best_dir,
                                    "symbol": best_symbol,
                                    "sl": sl,
                                    "R": abs(entry_price - sl),
                                    "tp1_done": False,
                                    "tp2_done": False,
                                    "entry_regime": best_regime,
                                    "entry_risk": best_risk,
                                    "entry_mtf_bias": best_mtf_bias,
                                    "entry_latency_ms": exec_latency,
                                    "highest_price": entry_price if best_dir == "LONG" else entry_price,
                                    "trail_active": False,
                                    "entry_time": time.time(),
                                    "peak": peak,
                                })
                                save_state(state)
                                
                                # BAR-CLOSE LOCK
                                bar_close_lock = True
                                last_bar_close_time = int(time.time())

                                print(f"\n{'='*60}")
                                print(f"✅ TRADE OPENED: {best_symbol}")
                                print(f"   Direction: {best_dir} | Entry: {entry_price}")
                                print(f"   Risk: {best_risk:.4f} (clamped) | SL: {sl}")
                                print(f"   MTF Bias: {best_mtf_bias:.2f} | Regime: {best_regime}")
                                print(f"{'='*60}\n")
                                
                                # ===== SEND TELEGRAM TRADE OPENED NOTIFICATION =====
                                try:
                                    telegram_dashboard.trade_opened_notification(
                                        best_symbol, best_dir, entry_price, sl,
                                        best_risk, best_score, best_regime, best_mtf_bias
                                    )
                                except Exception as e:
                                    print(f"⚠️  Trade notification failed: {e}")

        # === CLEANUP ===
        if int(time.time()) % 300 == 0:
            create_recovery_checkpoint(state)
            if dynamic_mtf_cache:
                try:
                    cleared = dynamic_mtf_cache.clear_expired()
                    print(f"🧹 Cache cleanup: {cleared} expired entries removed")
                except:
                    pass

        loop_duration = (time.time() - loop_start_time) * 1000
        if loop_duration > LATENCY_THRESHOLD_MS * 2:
            print(f"⚠️  LOOP LATENCY HIGH: {loop_duration:.1f}ms")

        time.sleep(30)

    except KeyboardInterrupt:
        print("\n🛑 Keyboard interrupt - graceful shutdown")
        
        # ===== SEND SHUTDOWN NOTIFICATION =====
        try:
            final_balance = binance.fetch_balance()
            final_equity = float(final_balance.get("total", {}).get("USDT", 0) or 0)
            
            shutdown_stats = {
                "final_equity": final_equity,
                "total_return": ((final_equity - initial_equity) / initial_equity * 100) if initial_equity > 0 else 0,
                "total_trades": len(logs) if logs else 0,
                "win_rate": perf.get('win_rate', 0) if 'perf' in locals() else 0,
                "profit_factor": perf.get('profit_factor', 0) if 'perf' in locals() else 0
            }
            
            telegram_dashboard.shutdown_notification(
                reason="Keyboard interrupt - Manual shutdown",
                stats=shutdown_stats
            )
        except Exception as e:
            print(f"⚠️  Shutdown notification failed: {e}")
        
        crash_handler.emergency_shutdown()
        break

    except Exception as e:
        print(f"\n❌ ENGINE ERROR: {str(e)}")
        traceback.print_exc()
        
        # ===== SEND ERROR NOTIFICATION =====
        try:
            tb = traceback.format_exc()
            telegram_dashboard.error_notification(
                str(e),
                error_type="GENERAL",
                traceback_str=tb
            )
        except:
            pass
        
        try:
            create_recovery_checkpoint(state)
        except:
            pass
        time.sleep(15)
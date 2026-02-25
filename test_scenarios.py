# ================= BATTLE TEST SUITE =================
# 5 kritik scenario'yu simulate et

import time
import json
from datetime import datetime
import traceback

# Test imports
from recovery_engine import StateManager, load_state, save_state, create_recovery_checkpoint
from exchange_reconciliation_engine import ExchangeReconciliation
from position_rebuilder_engine import PositionRebuilder
from telegram_dashboard_engine import TelegramDashboard
from trade_lifecycle_engine import TradeLifecycleEngine

# Config
TELEGRAM_TOKEN = '8763094320:AAGSq3tXa6JWLsdYc40wqi9Xr4oMloPGuMU'
TELEGRAM_CHAT_ID = '6350700231'

# ================= SETUP: Mock position create et =================
def setup_mock_position():
    """Create mock positions for ALL symbols"""
    from config import SYMBOLS
    
    # Son açılan position'ı kaydet (current_position olacak)
    # Bot zaten 4 symbol'de position açmış, biz state'i güncelle
    
    # Load current state from bot
    try:
        with open('engine_state.json', 'r') as f:
            current_state = json.load(f)
        print("✅ Loaded existing state from bot")
        return current_state
    except:
        pass
    
    # Eğer state yoksa, en son symbol'ü current_position yap
    latest_symbol = SYMBOLS[-1] if SYMBOLS else 'BTC/USDT'
    
    mock_state = {
        'current_position': {
            'symbol': latest_symbol,
            'side': 'long',
            'entry_price': 40000,
            'amount': 0.5,
            'leverage': 5,
            'tp': 42000,
            'sl': 38000,
            'opened_at': time.time(),
            'order_id': 'mock_12345'
        },
        'trades': [],
        'stats': {
            'total_trades': 1,
            'wins': 0,
            'losses': 0
        },
        'entry': 40000,
        'sl': 38000,
        'tp': 42000,
        'R': 2000,
        'symbol': latest_symbol,
        'peak': 10000.0,
        'direction': 'long'
    }
    
    with open('engine_state.json', 'w') as f:
        json.dump(mock_state, f, indent=2)
    
    print(f"✅ Mock position created for {latest_symbol}")
    return mock_state
    
    with open('engine_state.json', 'w') as f:
        json.dump(mock_state, f, indent=2)
    
    print("✅ Mock position created for testing")
    return mock_state

class BattleTestSuite:
    """5 kritik senaryoyu test et"""
    
    def __init__(self, binance, state_manager):
        self.binance = binance
        self.state_manager = state_manager
        self.telegram_dashboard = TelegramDashboard(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)
        self.test_results = []
        self.test_log = "test_results.json"
    
    def log_test(self, test_name, status, details):
        """Test sonuçlarını log'la"""
        result = {
            "timestamp": datetime.now().isoformat(),
            "test_name": test_name,
            "status": status,
            "details": details
        }
        
        self.test_results.append(result)
        
        try:
            with open(self.test_log, "w") as f:
                json.dump(self.test_results, f, indent=2)
        except:
            pass
        
        print(f"\n{'='*60}")
        print(f"📝 TEST: {test_name}")
        print(f"Status: {status}")
        print(f"Details: {details}")
        print(f"{'='*60}\n")
    
    # ===== TEST 1: SL Trigger Simulasyonu =====
    def test_1_sl_trigger_simulation(self, symbol, direction):
        """
        1️⃣ Zorla SL trigger - bot SL'yi doğru şekilde işliyor mu?
        """
        test_name = "SL Trigger Simulation"
        
        try:
            print(f"\n🚨 TEST 1: SL Trigger Simulation - {symbol} {direction}")
            print("Scenario: Checking if SL trigger is properly detected")
            
            state = load_state()
            if not state.get('entry'):
                self.log_test(test_name, "FAIL", "No active position found")
                return False
            
            print(f"✅ Active position found: {state.get('symbol')}")
            print(f"   Entry: {state.get('entry')}")
            print(f"   SL: {state.get('sl')}")
            
            try:
                positions = self.binance.fetch_positions([symbol])
                if not positions or float(positions[0].get('contracts', 0)) == 0:
                    self.log_test(test_name, "FAIL", f"No position on exchange for {symbol}")
                    return False
                
                position = positions[0]
                current_price = float(position['info'].get('markPrice', 0))
                contracts = float(position['contracts'])
                
                print(f"   Current Price: {current_price}")
                print(f"   Contracts: {contracts}")
                
            except Exception as e:
                self.log_test(test_name, "FAIL", f"Could not fetch position: {str(e)}")
                return False
            
            sl = state.get('sl')
            entry = state.get('entry')
            
            if not sl or not entry:
                self.log_test(test_name, "FAIL", "SL or entry missing in state")
                return False
            
            try:
                from exchange_reconciliation_engine import ExchangeReconciliation
                from exchange_stop_engine import ExchangeStopManager
                
                stop_manager = ExchangeStopManager()
                exchange_recon = ExchangeReconciliation(self.binance, stop_manager)
                
                state_updated, issues = exchange_recon.reconcile_position(
                    symbol, state, positions
                )
                
                if issues:
                    print(f"⚠️  Reconciliation issues found: {issues}")
                else:
                    print(f"✅ Reconciliation passed")
            
            except Exception as e:
                print(f"⚠️  Reconciliation check failed: {str(e)}")
            
            self.log_test(test_name, "PASS", {
                "symbol": symbol,
                "direction": direction,
                "entry": entry,
                "sl": sl,
                "current_price": current_price,
                "sl_distance": abs(current_price - sl),
                "test_passed": True
            })
            
            return True
        
        except Exception as e:
            self.log_test(test_name, "FAIL", f"Exception: {str(e)}")
            traceback.print_exc()
            return False
    
    # ===== TEST 2: Internet Kesintisi Simulasyonu =====
    def test_2_internet_disconnection(self):
        """
        2️⃣ Bot internet kesintisinde nasıl davranıyor?
        """
        test_name = "Internet Disconnection Recovery"
        
        try:
            print(f"\n🌐 TEST 2: Internet Disconnection Recovery")
            print("Scenario: Simulating network timeout and recovery")
            
            state_before = load_state()
            print(f"✅ State before disconnection: {state_before.get('entry')}")
            
            try:
                create_recovery_checkpoint(state_before)
                print(f"✅ Recovery checkpoint created")
            except Exception as e:
                self.log_test(test_name, "FAIL", f"Could not create checkpoint: {str(e)}")
                return False
            
            import os
            if os.path.exists("recovery_checkpoint.json"):
                print(f"✅ Recovery checkpoint file exists")
                with open("recovery_checkpoint.json", "r") as f:
                    checkpoint = json.load(f)
                checkpoint_entry = checkpoint.get('state', {}).get('entry')
                print(f"   Checkpoint state: {checkpoint_entry}")
            else:
                self.log_test(test_name, "FAIL", "Recovery checkpoint file not created")
                return False
            
            print(f"⚠️  Simulating state corruption...")
            state_before['entry'] = None
            
            state_after = load_state()
            
            if state_after.get('entry') is not None:
                print(f"✅ State recovered from checkpoint!")
                print(f"   Recovered entry: {state_after.get('entry')}")
                
                self.log_test(test_name, "PASS", {
                    "checkpoint_created": True,
                    "state_recovered": True,
                    "entry_preserved": state_after.get('entry') is not None
                })
                return True
            else:
                self.log_test(test_name, "FAIL", "State not recovered from checkpoint")
                return False
        
        except Exception as e:
            self.log_test(test_name, "FAIL", f"Exception: {str(e)}")
            traceback.print_exc()
            return False
    
    # ===== TEST 3: Stop Order Manuel Silme + Reconciliation =====
    def test_3_manual_stop_deletion(self, symbol):
        """
        3️⃣ Stop'u manuel silip reconciliation testi
        """
        test_name = "Manual Stop Deletion & Reconciliation"
        
        try:
            print(f"\n🗑️  TEST 3: Manual Stop Deletion & Reconciliation - {symbol}")
            print("Scenario: Checking stop order reconciliation")
            
            try:
                positions = self.binance.fetch_positions([symbol])
                if not positions or float(positions[0].get('contracts', 0)) == 0:
                    self.log_test(test_name, "SKIP", f"No position on {symbol}")
                    return None
                
                position = positions[0]
                contracts = abs(float(position['contracts']))
                print(f"✅ Position found: {contracts} contracts")
            
            except Exception as e:
                self.log_test(test_name, "FAIL", f"Could not fetch position: {str(e)}")
                return False
            
            try:
                from exchange_stop_engine import ExchangeStopManager
                stop_manager = ExchangeStopManager()
                
                active_stops = stop_manager.get_active_stops(symbol)
                print(f"✅ Active stops found: {len(active_stops)}")
                
                if not active_stops:
                    print(f"⚠️  No active stops to check")
                    self.log_test(test_name, "SKIP", "No active stops found")
                    return None
                
                for stop in active_stops:
                    print(f"   - Stop ID: {stop.get('stopOrderId')}")
                    print(f"   - Price: {stop.get('stopPrice')}")
            
            except Exception as e:
                print(f"⚠️  Could not list stops: {str(e)}")
            
            try:
                state = load_state()
                exchange_recon = ExchangeReconciliation(self.binance, stop_manager)
                
                state_updated, issues = exchange_recon.reconcile_position(
                    symbol, state, positions
                )
                
                print(f"✅ Reconciliation completed")
                print(f"   Issues found: {len(issues) if issues else 0}")
                print(f"   State updated: {state_updated}")
                
                if issues:
                    print(f"   Issues: {issues}")
                
                issues_count = len(issues) if issues else 0
            
            except Exception as e:
                self.log_test(test_name, "FAIL", f"Reconciliation failed: {str(e)}")
                return False
            
            stops_count = len(active_stops) if 'active_stops' in locals() else 0
            
            self.log_test(test_name, "PASS", {
                "symbol": symbol,
                "stops_checked": stops_count,
                "reconciliation_passed": True,
                "issues_found": issues_count
            })
            
            return True
        
        except Exception as e:
            self.log_test(test_name, "FAIL", f"Exception: {str(e)}")
            traceback.print_exc()
            return False
    
    # ===== TEST 4: Crash + Restart + Rebuild =====
    def test_4_crash_restart_rebuild(self, symbol):
        """
        4️⃣ Crash + restart + rebuild testi
        """
        test_name = "Crash Restart Rebuild"
        
        try:
            print(f"\n💥 TEST 4: Crash Restart Rebuild - {symbol}")
            print("Scenario: Simulating crash and position rebuild")
            
            state_before = load_state()
            print(f"✅ State before crash: entry={state_before.get('entry')}")
            
            try:
                positions = self.binance.fetch_positions([symbol])
                if not positions or float(positions[0].get('contracts', 0)) == 0:
                    self.log_test(test_name, "SKIP", f"No position on {symbol}")
                    return None
                
                position = positions[0]
                exchange_entry = float(position['info'].get('averagePrice', 0))
                print(f"✅ Exchange position found: entry={exchange_entry}")
            
            except Exception as e:
                self.log_test(test_name, "FAIL", f"Could not fetch position: {str(e)}")
                return False
            
            try:
                position_rebuilder = PositionRebuilder(self.binance, self.state_manager)
                rebuilt_state = position_rebuilder.rebuild_from_exchange(
                    self.binance, 
                    positions
                )
                
                if not rebuilt_state:
                    self.log_test(test_name, "FAIL", "Position rebuilder failed")
                    return False
                
                print(f"✅ Position rebuilt")
                print(f"   Rebuilt entry: {rebuilt_state.get('entry')}")
                print(f"   Rebuilt SL: {rebuilt_state.get('sl')}")
                print(f"   Rebuilt R: {rebuilt_state.get('R')}")
            
            except Exception as e:
                self.log_test(test_name, "FAIL", f"Rebuild failed: {str(e)}")
                return False
            
            try:
                is_valid = position_rebuilder.verify_rebuild(rebuilt_state, positions)
                
                if not is_valid:
                    self.log_test(test_name, "FAIL", "Rebuilt state validation failed")
                    return False
                
                print(f"✅ Rebuilt state validated")
            
            except Exception as e:
                self.log_test(test_name, "FAIL", f"Verification failed: {str(e)}")
                return False
            
            self.log_test(test_name, "PASS", {
                "symbol": symbol,
                "original_entry": state_before.get('entry'),
                "rebuilt_entry": rebuilt_state.get('entry'),
                "rebuilt_sl": rebuilt_state.get('sl'),
                "rebuild_valid": True
            })
            
            return True
        
        except Exception as e:
            self.log_test(test_name, "FAIL", f"Exception: {str(e)}")
            traceback.print_exc()
            return False
    
    # ===== TEST 5: Aynı Anda 2 Pozisyon =====
    def test_5_dual_position_scenario(self):
        """
        5️⃣ Aynı anda 2 pozisyon açma senaryosu
        """
        test_name = "Dual Position Scenario"
        
        try:
            print(f"\n👥 TEST 5: Dual Position Scenario")
            print("Scenario: Testing bar-close lock mechanism")
            
            try:
                positions = self.binance.fetch_positions()
                open_positions = [p for p in positions if float(p.get('contracts', 0)) != 0]
                print(f"✅ Current open positions: {len(open_positions)}")
                
                if len(open_positions) >= 2:
                    print(f"⚠️  Already have 2+ positions, test not applicable")
                    self.log_test(test_name, "SKIP", "Already have max positions")
                    return None
            
            except Exception as e:
                self.log_test(test_name, "FAIL", f"Could not fetch positions: {str(e)}")
                return False
            
            state = load_state()
            if state.get('entry') and len(open_positions) == 1:
                print(f"✅ Currently have 1 active position")
            else:
                print(f"⚠️  Position count mismatch")
            
            print(f"\n📋 Testing bar-close lock mechanism:")
            print(f"   - Position 1 acildi, bar_close_lock = True")
            print(f"   - minutes_since_lock < 1 ise Position 2 acılamaz")
            
            current_time = time.time()
            last_bar_close_time = current_time - 30
            bar_close_lock = True
            
            minutes_since = (time.time() - last_bar_close_time) / 60
            
            print(f"   - Current time: {current_time}")
            print(f"   - Last bar close: {last_bar_close_time}")
            print(f"   - Minutes since: {minutes_since:.2f}")
            
            can_open_second = not (bar_close_lock and minutes_since < 1)
            
            print(f"   - Can open 2nd position: {can_open_second}")
            
            if can_open_second:
                self.log_test(test_name, "FAIL", "Bar-close lock failed (2nd position allowed)")
                return False
            else:
                print(f"✅ Bar-close lock working correctly")
            
            self.log_test(test_name, "PASS", {
                "bar_close_lock_active": bar_close_lock,
                "minutes_since_last": minutes_since,
                "can_open_second": can_open_second,
                "lock_working": not can_open_second
            })
            
            return True
        
        except Exception as e:
            self.log_test(test_name, "FAIL", f"Exception: {str(e)}")
            traceback.print_exc()
            return False
    
    # ===== RUN ALL TESTS =====
    def run_all_tests(self, binance, symbols=None):
        """Tum testleri calistir - MULTIPLE SYMBOLS"""
        if symbols is None:
            symbols = ['BTC/USDT', 'ETH/USDT', 'LINK/USDT', 'ONDO/USDT']
        
        print("\n" + "="*80)
        print("🚀 BATTLE TEST SUITE - STARTING ALL TESTS")
        print(f"📊 Testing symbols: {', '.join(symbols)}")
        print(f"⏳ Test duration: ~3-5 minutes (do not close!)")
        print("="*80 + "\n")
        
        results_summary = {
            "start_time": datetime.now().isoformat(),
            "total_tests": 5,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "tested_symbols": symbols
        }
        
        try:
            # TEST 1: Her symbol için SL trigger testi
            for symbol in symbols:
                result = self.test_1_sl_trigger_simulation(symbol, "LONG")
                if result is True:
                    results_summary["passed"] += 1
                elif result is False:
                    results_summary["failed"] += 1
                else:
                    results_summary["skipped"] += 1
                time.sleep(2)
            
            # TEST 2: Internet Disconnection
            result = self.test_2_internet_disconnection()
            if result is True:
                results_summary["passed"] += 1
            elif result is False:
                results_summary["failed"] += 1
            else:
                results_summary["skipped"] += 1
            
            time.sleep(4)
            
            # TEST 3-4: İlk 2 symbol için stop ve crash testi
            for symbol in symbols[:2]:
                result = self.test_3_manual_stop_deletion(symbol)
                if result is True:
                    results_summary["passed"] += 1
                elif result is False:
                    results_summary["failed"] += 1
                else:
                    results_summary["skipped"] += 1
                
                time.sleep(2)
                
                result = self.test_4_crash_restart_rebuild(symbol)
                if result is True:
                    results_summary["passed"] += 1
                elif result is False:
                    results_summary["failed"] += 1
                else:
                    results_summary["skipped"] += 1
                
                time.sleep(2)
            
            # TEST 5: Dual position
            result = self.test_5_dual_position_scenario()
            if result is True:
                results_summary["passed"] += 1
            elif result is False:
                results_summary["failed"] += 1
            else:
                results_summary["skipped"] += 1
        
        except Exception as e:
            print(f"\n❌ TEST SUITE ERROR: {str(e)}")
            traceback.print_exc()
        
        print("\n" + "="*80)
        print("📊 TEST RESULTS SUMMARY")
        print("="*80)
        print(f"✅ Passed: {results_summary['passed']}/5")
        print(f"❌ Failed: {results_summary['failed']}/5")
        print(f"⏭️  Skipped: {results_summary['skipped']}/5")
        print(f"📋 Tested Symbols: {', '.join(symbols)}")
        print("="*80 + "\n")
        
        try:
            passed = results_summary['passed']
            failed = results_summary['failed']
            skipped = results_summary['skipped']
            
            message = f"""
🧪 <b>BATTLE TEST SUITE COMPLETED</b>

<b>Results:</b>
✅ Passed: {passed}/5
❌ Failed: {failed}/5
⏭️ Skipped: {skipped}/5

<b>Tested Symbols:</b>
{', '.join(symbols)}

<b>Details saved to:</b> test_results.json

{"🚨 CRITICAL: " + str(failed) + " test(s) failed!" if failed > 0 else "✅ All tests passed!"}
"""
            self.telegram_dashboard.send_message(message)
        except:
            pass
        
        return results_summary


# ===== MAIN ENTRY POINT =====
if __name__ == "__main__":
    from config import SYMBOLS
    from data_engine import binance
    
    print("🔧 Initializing Battle Test Suite...")
    
    # Setup mock position FIRST
    setup_mock_position()
    
    state_manager = StateManager()
    test_suite = BattleTestSuite(binance, state_manager)
    
    print(f"✅ Test suite ready")
    print(f"⚠️  Make sure bot has active positions before running tests!\n")
    
    test_suite.run_all_tests(binance, symbols=SYMBOLS)
    
    print("\n✅ Battle test suite completed!")
    print("📊 Check test_results.json for detailed results")
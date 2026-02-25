# ================= CRASH DETECTION & RECOVERY ENGINE =================
import signal
import sys
import traceback
from datetime import datetime
import json
import os

class CrashRecoveryHandler:
    """
    Crash detection, logging, state saving.
    Graceful shutdown sağlar.
    """
    
    def __init__(self, state_manager, binance, symbols):
        self.state_manager = state_manager
        self.binance = binance
        self.symbols = symbols
        self.crash_log_file = "crash_logs.json"
        
        signal.signal(signal.SIGINT, self._handle_crash)
        signal.signal(signal.SIGTERM, self._handle_crash)
    
    def _handle_crash(self, signum, frame):
        """Crash handler - graceful shutdown"""
        print("\n" + "="*80)
        print("🚨 CRASH DETECTED - INITIATING RECOVERY SEQUENCE")
        print("="*80)
        
        self.emergency_shutdown()
        sys.exit(0)
    
    def emergency_shutdown(self):
        """Emergency shutdown"""
        try:
            print("\n📋 EMERGENCY SHUTDOWN SEQUENCE:")
            print("1️⃣ Saving current state...")
            
            from state_manager_enhanced import state_manager
            state = state_manager.load_state()
            state_manager.create_recovery_checkpoint(state)
            
            print("2️⃣ Documenting open positions...")
            try:
                positions = self.binance.fetch_positions()
                open_positions = [p for p in positions if float(p.get("contracts", 0)) != 0]
                
                if open_positions:
                    print(f"   ⚠️ Found {len(open_positions)} open position(s):")
                    for pos in open_positions:
                        symbol = pos["symbol"]
                        contracts = float(pos.get("contracts", 0))
                        print(f"      - {symbol}: {contracts} contracts")
            except Exception as e:
                print(f"   ⚠️ Could not fetch positions: {e}")
            
            print("3️⃣ Logging crash information...")
            self._log_crash(state)
            
            print("4️⃣ Checking exchange orders...")
            self._check_exchange_orders()
            
            print("\n✅ EMERGENCY SHUTDOWN COMPLETE")
            print("   Recovery data saved. Next startup will auto-recover.\n")
        
        except Exception as e:
            print(f"❌ Emergency shutdown error: {e}")
            traceback.print_exc()
    
    def _log_crash(self, state):
        """Crash'ı log'a kaydet"""
        try:
            crash_info = {
                "timestamp": datetime.now().isoformat(),
                "state": state,
                "traceback": traceback.format_exc(),
                "recovery_available": True
            }
            
            crash_logs = []
            if os.path.exists(self.crash_log_file):
                try:
                    with open(self.crash_log_file, "r") as f:
                        crash_logs = json.load(f)
                except:
                    pass
            
            crash_logs.append(crash_info)
            
            with open(self.crash_log_file, "w") as f:
                json.dump(crash_logs[-100:], f, indent=2)
            
            print(f"   📝 Crash logged to {self.crash_log_file}")
        
        except Exception as e:
            print(f"   ⚠️ Crash logging failed: {e}")
    
    def _check_exchange_orders(self):
        """Exchange'deki açık order'ları kontrol et"""
        try:
            for symbol in self.symbols[:3]:
                try:
                    orders = self.binance.fetch_open_orders(symbol)
                    if orders:
                        print(f"   ⚠️ {symbol}: {len(orders)} open order(s)")
                except:
                    pass
        except Exception as e:
            print(f"   ⚠️ Could not check orders: {e}")

def initialize_crash_recovery(state_manager, binance, symbols):
    """Crash recovery handler'ı initialize et"""
    handler = CrashRecoveryHandler(state_manager, binance, symbols)
    return handler
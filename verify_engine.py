# ================= RECOVERY VERIFICATION ENGINE =================
import json
import os
from datetime import datetime

class RecoveryVerifier:
    """Recovery doğrulama"""
    
    def __init__(self, binance, state_manager, stop_manager=None):
        self.binance = binance
        self.state_manager = state_manager
        self.stop_manager = stop_manager
    
    def verify_recovery(self, symbols):
        """Complete recovery verification"""
        print("\n" + "="*80)
        print("🔍 RECOVERY VERIFICATION")
        print("="*80)
        
        recovery_status = self.state_manager.get_recovery_status()
        
        print("\n📊 Recovery Status:")
        print(f"   Main state exists: {recovery_status['main_state_exists']}")
        print(f"   Recovery checkpoint exists: {recovery_status['recovery_checkpoint_exists']}")
        print(f"   Available backups: {recovery_status['backup_count']}")
        
        if recovery_status['recovery_checkpoint_exists']:
            print("\n⚠️ RECOVERY MODE DETECTED")
        
        print("\n1️⃣ Checking exchange positions...")
        exchange_positions = self._check_exchange_positions(symbols)
        
        print("\n2️⃣ Checking local state...")
        local_state = self.state_manager.load_state()
        
        print("\n3️⃣ Reconciling states...")
        reconciliation = self._reconcile_states(exchange_positions, local_state)
        
        print("\n4️⃣ Verifying stops...")
        stop_verification = self._verify_stops(symbols)
        
        print("\n" + "="*80)
        print("✅ VERIFICATION COMPLETE")
        print("="*80)
        
        return {
            "exchange_positions": exchange_positions,
            "local_state": local_state,
            "reconciliation": reconciliation,
            "stops": stop_verification,
            "recovery_safe": reconciliation["consistent"]
        }
    
    def _check_exchange_positions(self, symbols):
        """Exchange pozisyonları kontrol"""
        try:
            positions = self.binance.fetch_positions()
            open_positions = [
                {
                    "symbol": p["symbol"],
                    "contracts": float(p.get("contracts", 0)),
                    "direction": "LONG" if float(p.get("contracts", 0)) > 0 else "SHORT",
                }
                for p in positions if float(p.get("contracts", 0)) != 0
            ]
            
            print(f"   Found {len(open_positions)} open position(s)")
            for pos in open_positions:
                print(f"      - {pos['symbol']}: {pos['contracts']}")
            
            return open_positions
        
        except Exception as e:
            print(f"   Error: {e}")
            return []
    
    def _reconcile_states(self, exchange_positions, local_state):
        """State reconciliation"""
        reconciliation = {
            "consistent": True,
            "issues": [],
            "warnings": []
        }
        
        if local_state.get("entry"):
            if not exchange_positions:
                reconciliation["issues"].append(
                    "Local has entry but no exchange positions"
                )
                reconciliation["consistent"] = False
        
        if len(exchange_positions) > 1:
            reconciliation["warnings"].append(
                f"Multiple positions open: {len(exchange_positions)}"
            )
        
        if reconciliation["issues"]:
            print("   ❌ ISSUES FOUND:")
            for issue in reconciliation["issues"]:
                print(f"      - {issue}")
        
        if not reconciliation["issues"]:
            print("   ✅ States consistent")
        
        return reconciliation
    
    def _verify_stops(self, symbols):
        """Stop order verification"""
        try:
            stops_found = {}
            
            for symbol in symbols[:5]:
                try:
                    orders = self.binance.fetch_open_orders(symbol)
                    stop_orders = [
                        o for o in orders
                        if "stop" in str(o.get("type", "")).lower()
                    ]
                    
                    if stop_orders:
                        stops_found[symbol] = len(stop_orders)
                        print(f"   ✅ {symbol}: {len(stop_orders)} STOP(s)")
                
                except:
                    pass
            
            if not stops_found:
                print("   ⚠️ No STOP orders found")
            
            return stops_found
        
        except Exception as e:
            print(f"   Error: {e}")
            return {}
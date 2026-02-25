# ================= EXCHANGE RECONCILIATION ENGINE =================
# State ↔ Exchange senkronizasyonu (iki yönlü)

import json
import time
from datetime import datetime

class ExchangeReconciliation:
    """
    State ve Exchange her zaman sync olmalı
    
    Sorun:
    - State'te SL var ama exchange'de farklı
    - Partial TP sonrası position reduce oldu ama state bilmiyor
    - Stop order düştü ama state güncellenmiyor
    
    Çözüm:
    - Her loop'ta: Exchange → State check
    - Fark varsa: Exchange'i source of truth kabul et
    - Stop manager ile double-check
    """
    
    def __init__(self, binance, stop_manager=None):
        self.binance = binance
        self.stop_manager = stop_manager
        self.recon_log = "exchange_reconciliation_log.json"
        self.last_recon = {}
    
    def reconcile_position(self, symbol, state, open_positions):
        """
        Açık pozisyonu exchange'deki gerçek verilere göre reconcile et
        
        Args:
            symbol: Trading pair
            state: Current state dict
            open_positions: Exchange'den gelen positions
            
        Returns:
            tuple: (state_updated, issues_found)
        """
        issues = []
        state_updated = False
        
        try:
            # 1️⃣ Exchange'den gerçek pozisyon al
            exchange_position = None
            if open_positions:
                exchange_position = next(
                    (p for p in open_positions if p['symbol'] == symbol), 
                    None
                )
            
            if not exchange_position:
                print(f"⚠️  Position not found on exchange: {symbol}")
                issues.append("position_not_found_on_exchange")
                return state, issues
            
            # 2️⃣ Exchange pozisyon detayları
            exchange_contracts = float(exchange_position.get('contracts', 0))
            exchange_entry = float(exchange_position.get('info', {}).get('averagePrice', 0))
            exchange_margin = float(exchange_position.get('initialMargin', 0))
            exchange_unrealized = float(exchange_position.get('unrealizedPnl', 0))
            
            # 3️⃣ State pozisyon detayları
            state_entry = state.get('entry')
            state_sl = state.get('sl')
            state_direction = state.get('direction')
            
            # ===== KONTROLLER =====
            
            # A) Entry price kontrolü
            if state_entry and exchange_entry:
                entry_diff = abs(exchange_entry - state_entry) / exchange_entry
                if entry_diff > 0.01:  # %1 tolerance
                    print(f"⚠️  Entry price mismatch!")
                    print(f"    Exchange: {exchange_entry}")
                    print(f"    State: {state_entry}")
                    print(f"    Difference: {entry_diff*100:.2f}%")
                    issues.append("entry_price_mismatch")
                    
                    # Exchange'i source of truth kabul et
                    state['entry'] = exchange_entry
                    state_updated = True
            
            # B) Position size kontrolü
            state_contracts = abs(float(exchange_contracts))
            if state_contracts != abs(float(exchange_contracts)):
                print(f"⚠️  Position size mismatch!")
                print(f"    Exchange: {exchange_contracts}")
                print(f"    State implied: {state_contracts}")
                issues.append("position_size_mismatch")
                # State'te position size yok, bu normal
            
            # C) SL/TP kontrolü (Eğer stop order var ise)
            if self.stop_manager and state_sl:
                try:
                    # Stop manager'dan active stop al
                    active_stops = self.stop_manager.get_active_stops(symbol)
                    
                    if active_stops:
                        stop_price = active_stops[0].get('stopPrice')
                        
                        if stop_price and state_sl:
                            sl_diff = abs(stop_price - state_sl) / state_sl
                            
                            if sl_diff > 0.005:  # %0.5 tolerance
                                print(f"⚠️  SL (Stop) mismatch!")
                                print(f"    Exchange stop: {stop_price}")
                                print(f"    State SL: {state_sl}")
                                issues.append("sl_stop_mismatch")
                                
                                # Exchange'deki stop gerçek, state'i güncelle
                                state['sl'] = stop_price
                                state_updated = True
                    
                except Exception as e:
                    print(f"⚠️  Could not verify stop orders: {e}")
                
                # D) Unrealized PnL kontrolü
                if state_entry and exchange_contracts > 0:
                    if state_direction == "LONG":
                        calculated_pnl = (exchange_entry - state_entry) * exchange_contracts
                    else:
                        calculated_pnl = (state_entry - exchange_entry) * exchange_contracts
                    
                    pnl_diff = abs(calculated_pnl - exchange_unrealized)
                    
                    if pnl_diff > (state_entry * 0.005):  # %0.5 tolerance
                        print(f"⚠️  Unrealized PnL mismatch!")
                        print(f"    Exchange: {exchange_unrealized}")
                        print(f"    Calculated: {calculated_pnl}")
                        issues.append("unrealized_pnl_mismatch")
                        
                        # Bu normally trade'in partial close oldu anlamı
                        # State'i güncelle ama warning ver
                        state['exchange_unrealized_pnl'] = exchange_unrealized
                        state_updated = True
                
                # E) TP1 / TP2 kontrol et
                # Eğer unrealized PnL R'nin ötesindeyse, TP yapılmış demek
                if state.get('R') and exchange_unrealized > 0:
                    
                    # TP1: +1R
                    tp1_profit = state['R'] * exchange_contracts
                    if exchange_unrealized > tp1_profit * 0.9 and not state.get('tp1_done'):
                        print(f"✅ TP1 detected on exchange (unrealized: {exchange_unrealized})")
                        state['tp1_done'] = True
                        state_updated = True
                    
                    # TP2: +2R
                    tp2_profit = state['R'] * 2 * exchange_contracts
                    if exchange_unrealized > tp2_profit * 0.9 and not state.get('tp2_done'):
                        print(f"✅ TP2 detected on exchange (unrealized: {exchange_unrealized})")
                        state['tp2_done'] = True
                        state_updated = True
            
            # ===== LOG =====
            self._log_reconciliation({
                "timestamp": datetime.now().isoformat(),
                "symbol": symbol,
                "issues_found": len(issues),
                "issues": issues,
                "state_updated": state_updated,
                "exchange_entry": exchange_entry,
                "state_entry": state_entry,
                "exchange_unrealized": exchange_unrealized
            })
            
            if issues:
                print(f"⚠️  Reconciliation found {len(issues)} issues")
                for issue in issues:
                    print(f"    - {issue}")
            else:
                print(f"✅ Reconciliation OK for {symbol}")
            
            return state, issues
        
        except Exception as e:
            print(f"❌ Reconciliation failed: {e}")
            self._log_reconciliation({
                "timestamp": datetime.now().isoformat(),
                "symbol": symbol,
                "error": str(e),
                "status": "FAILED"
            })
            return state, ["reconciliation_error"]
    
    def reconcile_all_positions(self, state, open_positions):
        """
        Tüm açık pozisyonları reconcile et
        
        Returns:
            tuple: (state_updated, total_issues)
        """
        state_updated = False
        total_issues = []
        
        if not open_positions:
            print("✅ No open positions to reconcile")
            return state_updated, total_issues
        
        for position in open_positions:
            symbol = position['symbol']
            contracts = float(position.get('contracts', 0))
            
            if contracts == 0:
                continue
            
            updated, issues = self.reconcile_position(symbol, state, open_positions)
            
            if issues:
                total_issues.extend(issues)
            
            if updated:
                state_updated = True
        
        return state_updated, total_issues
    
    def verify_stops_synchronized(self, symbol, state, expected_stops=1):
        """
        Stop order'lar state'le senkron mu kontrol et
        
        Args:
            symbol: Trading pair
            state: State dict
            expected_stops: Kaç stop order bekliyoruz?
            
        Returns:
            bool: Synchronized?
        """
        if not self.stop_manager:
            return True  # Stop manager yok, skip
        
        try:
            active_stops = self.stop_manager.get_active_stops(symbol)
            
            if len(active_stops) != expected_stops:
                print(f"⚠️  Stop count mismatch!")
                print(f"    Expected: {expected_stops}")
                print(f"    Found: {len(active_stops)}")
                return False
            
            if active_stops and state.get('sl'):
                stop_price = active_stops[0].get('stopPrice')
                state_sl = state.get('sl')
                
                if abs(stop_price - state_sl) / state_sl > 0.005:  # %0.5
                    print(f"⚠️  Stop price not synchronized!")
                    return False
            
            print(f"✅ Stops synchronized for {symbol}")
            return True
        
        except Exception as e:
            print(f"⚠️  Could not verify stops: {e}")
            return False
    
    def force_resync_stops(self, symbol, state, direction, contracts):
        """
        Stop order'ları force resync et (emergency)
        
        Kullanış:
        - Eğer state ve exchange'de büyük fark varsa
        - Exchange'deki stop silin, yenisini koy
        """
        if not self.stop_manager:
            print("❌ Stop manager not available")
            return False
        
        try:
            print(f"🔄 Force resyncing stops for {symbol}...")
            
            # 1️⃣ Eski stop'ları sil
            active_stops = self.stop_manager.get_active_stops(symbol)
            for stop in active_stops:
                try:
                    self.stop_manager.cancel_stop_order(
                        self.binance, 
                        symbol, 
                        stop.get('stopOrderId')
                    )
                except:
                    pass
            
            # 2️⃣ Yenisini koy
            if state.get('sl'):
                self.stop_manager.place_stop_order(
                    self.binance,
                    symbol,
                    direction,
                    state['sl'],
                    contracts
                )
                print(f"✅ Force resync completed")
                return True
        
        except Exception as e:
            print(f"❌ Force resync failed: {e}")
            return False
    
    def _log_reconciliation(self, log_entry):
        """Log reconciliation"""
        try:
            logs = []
            try:
                with open(self.recon_log, "r") as f:
                    logs = json.load(f)
            except:
                logs = []
            
            logs.append(log_entry)
            
            # Son 200 log tutun
            if len(logs) > 200:
                logs = logs[-200:]
            
            with open(self.recon_log, "w") as f:
                json.dump(logs, f, indent=2)
        except:
            pass
    
    def get_reconciliation_status(self):
        """Reconciliation status'u al"""
        try:
            with open(self.recon_log, "r") as f:
                logs = json.load(f)
            
            recent = logs[-10:] if logs else []
            issues_count = sum(1 for log in recent if log.get('issues_found', 0) > 0)
            
            return {
                "total_reconciliations": len(logs),
                "recent_10_reconciliations": len(recent),
                "recent_with_issues": issues_count,
                "last_reconciliation": logs[-1] if logs else None
            }
        except:
            return {
                "total_reconciliations": 0,
                "recent_10_reconciliations": 0,
                "recent_with_issues": 0,
                "last_reconciliation": None
            }
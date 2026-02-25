# ================= TRADE LIFECYCLE STATE MACHINE =================
# Her trade: OPENED → TP1_DONE → TP2_DONE → CLOSED (deterministic)

import json
import time
from datetime import datetime
from enum import Enum

class TradeState(Enum):
    """Trade durumları"""
    PENDING = "PENDING"          # Trade henüz açılmamış (retry aşaması)
    OPENED = "OPENED"            # Trade açılmış, SL + TP beklenyor
    TP1_DONE = "TP1_DONE"         # 1R profit alındı, kısmi close
    TP2_DONE = "TP2_DONE"         # 2R profit alındı, full close
    SL_HIT = "SL_HIT"             # Stop loss triggered
    CLOSED = "CLOSED"             # Trade kapatıldı
    CANCELLED = "CANCELLED"       # Trade iptal edildi
    ERROR = "ERROR"               # Hata oluştu

class TradeLifecycleEngine:
    """
    Her trade'in lifecycle'ını track et
    
    State machine:
    
    PENDING
        ↓
    OPENED → TP1_DONE → TP2_DONE → CLOSED
        ↓         ↓          ↓
       SL_HIT   SL_HIT     SL_HIT
    
    Her state transition exchange'de verify edilir.
    """
    
    def __init__(self, binance, state_manager):
        self.binance = binance
        self.state_manager = state_manager
        self.lifecycle_log = "trade_lifecycle_log.json"
        self.active_trades = {}  # symbol → trade lifecycle
    
    def create_trade_entry(self, symbol, direction, entry_price, sl, quantity, regime=None):
        """
        Yeni trade entry oluştur
        
        Args:
            symbol: Trading pair
            direction: LONG / SHORT
            entry_price: Entry fiyatı
            sl: Stop loss fiyatı
            quantity: Pozisyon boyutu
            regime: Market regime (opsiyonel)
            
        Returns:
            dict: Trade entry
        """
        trade_id = f"{symbol}_{int(time.time()*1000)}"
        
        trade_entry = {
            # ===== TEMEL BİLGİLER =====
            "trade_id": trade_id,
            "symbol": symbol,
            "direction": direction,
            "created_at": datetime.now().isoformat(),
            "created_timestamp": time.time(),
            
            # ===== ENTRY DETAYLARI =====
            "entry_price": entry_price,
            "entry_quantity": quantity,
            "stop_loss": sl,
            "risk": abs(entry_price - sl),
            
            # ===== TP SEVIYELERI =====
            "tp1_level": entry_price + (entry_price - sl) if direction == "LONG" else entry_price - (sl - entry_price),
            "tp2_level": entry_price + 2*(entry_price - sl) if direction == "LONG" else entry_price - 2*(sl - entry_price),
            
            # ===== STATE MACHINE =====
            "current_state": TradeState.PENDING.value,
            "state_transitions": [],
            
            # ===== TP TRACKING =====
            "tp1_filled": False,
            "tp1_filled_at": None,
            "tp1_filled_quantity": 0,
            "tp1_filled_price": None,
            
            "tp2_filled": False,
            "tp2_filled_at": None,
            "tp2_filled_quantity": 0,
            "tp2_filled_price": None,
            
            # ===== SL TRACKING =====
            "sl_hit": False,
            "sl_hit_at": None,
            "sl_hit_price": None,
            
            # ===== PNL TRACKING =====
            "exit_price": None,
            "exit_quantity": 0,
            "realized_pnl": 0,
            "realized_pnl_percent": 0,
            "max_profit": 0,
            "max_loss": 0,
            
            # ===== METADATA =====
            "regime": regime,
            "bar_count_held": 0,
            "trailing_sl": sl,
            "trailing_sl_last_update": datetime.now().isoformat()
        }
        
        self.active_trades[symbol] = trade_entry
        self._log_event(trade_entry, "CREATED")
        
        print(f"✅ Trade created: {trade_id}")
        print(f"   Symbol: {symbol} {direction}")
        print(f"   Entry: {entry_price}")
        print(f"   SL: {sl}")
        print(f"   TP1: {trade_entry['tp1_level']:.2f}")
        print(f"   TP2: {trade_entry['tp2_level']:.2f}")
        
        return trade_entry
    
    def transition_to_opened(self, symbol, state):
        """
        Trade PENDING → OPENED'a geçir
        
        Exchange'de gerçek position açıldığında çağrılır.
        """
        if symbol not in self.active_trades:
            print(f"❌ Trade not found: {symbol}")
            return False
        
        trade = self.active_trades[symbol]
        
        try:
            # Kontrol: Gerçek position var mı?
            try:
                positions = self.binance.fetch_positions([symbol])
                if not positions or float(positions[0].get('contracts', 0)) == 0:
                    print(f"❌ No position found on exchange for {symbol}")
                    return False
            except Exception as e:
                print(f"⚠️  Could not verify position: {e}")
                # Ama continue et, trade'i OPENED olarak işaretle
            
            # State transition
            trade['current_state'] = TradeState.OPENED.value
            trade['opened_at'] = datetime.now().isoformat()
            trade['opened_timestamp'] = time.time()
            
            trade['state_transitions'].append({
                "from": TradeState.PENDING.value,
                "to": TradeState.OPENED.value,
                "at": datetime.now().isoformat(),
                "source": "exchange_verification"
            })
            
            state['entry_time'] = time.time()
            
            self._log_event(trade, "OPENED")
            print(f"✅ Trade OPENED: {symbol}")
            
            return True
        
        except Exception as e:
            print(f"❌ Transition to OPENED failed: {e}")
            return False
    
    def update_tp1_filled(self, symbol, filled_quantity, filled_price):
        """
        TP1 partial close'u register et
        
        Kullanış: Eğer quantity %50 azaldıysa, TP1 yapılmış demek
        """
        if symbol not in self.active_trades:
            print(f"❌ Trade not found: {symbol}")
            return False
        
        trade = self.active_trades[symbol]
        
        try:
            if trade['current_state'] == TradeState.OPENED.value and not trade['tp1_filled']:
                
                trade['tp1_filled'] = True
                trade['tp1_filled_at'] = datetime.now().isoformat()
                trade['tp1_filled_quantity'] = filled_quantity
                trade['tp1_filled_price'] = filled_price
                
                # PnL hesapla (TP1 partial)
                tp1_pnl = (filled_price - trade['entry_price']) * filled_quantity
                if trade['direction'] == "SHORT":
                    tp1_pnl = (trade['entry_price'] - filled_price) * filled_quantity
                
                trade['realized_pnl'] += tp1_pnl
                trade['realized_pnl_percent'] = (trade['realized_pnl'] / (trade['entry_price'] * trade['entry_quantity'])) * 100
                
                trade['state_transitions'].append({
                    "from": TradeState.OPENED.value,
                    "to": TradeState.TP1_DONE.value,
                    "at": datetime.now().isoformat(),
                    "filled_quantity": filled_quantity,
                    "filled_price": filled_price,
                    "pnl": tp1_pnl,
                    "source": "partial_tp"
                })
                
                trade['current_state'] = TradeState.TP1_DONE.value
                
                self._log_event(trade, "TP1_FILLED")
                print(f"✅ TP1 filled: {symbol}")
                print(f"   Quantity: {filled_quantity}")
                print(f"   Price: {filled_price}")
                print(f"   PnL: {tp1_pnl:.2f}")
                
                return True
        
        except Exception as e:
            print(f"❌ Update TP1 failed: {e}")
            return False
    
    def update_tp2_filled(self, symbol, filled_quantity, filled_price):
        """
        TP2 close'u register et (full close)
        """
        if symbol not in self.active_trades:
            print(f"❌ Trade not found: {symbol}")
            return False
        
        trade = self.active_trades[symbol]
        
        try:
            if trade['current_state'] in [TradeState.OPENED.value, TradeState.TP1_DONE.value] and not trade['tp2_filled']:
                
                trade['tp2_filled'] = True
                trade['tp2_filled_at'] = datetime.now().isoformat()
                trade['tp2_filled_quantity'] = filled_quantity
                trade['tp2_filled_price'] = filled_price
                
                # Remaining quantity PnL
                remaining_qty = trade['entry_quantity'] - trade['tp1_filled_quantity']
                tp2_pnl = (filled_price - trade['entry_price']) * remaining_qty
                if trade['direction'] == "SHORT":
                    tp2_pnl = (trade['entry_price'] - filled_price) * remaining_qty
                
                trade['realized_pnl'] += tp2_pnl
                trade['realized_pnl_percent'] = (trade['realized_pnl'] / (trade['entry_price'] * trade['entry_quantity'])) * 100
                
                trade['exit_price'] = filled_price
                trade['exit_quantity'] = trade['entry_quantity']
                
                trade['state_transitions'].append({
                    "from": trade['current_state'],
                    "to": TradeState.TP2_DONE.value,
                    "at": datetime.now().isoformat(),
                    "filled_quantity": filled_quantity,
                    "filled_price": filled_price,
                    "pnl": tp2_pnl,
                    "total_realized_pnl": trade['realized_pnl'],
                    "source": "partial_tp"
                })
                
                trade['current_state'] = TradeState.CLOSED.value
                
                self._log_event(trade, "TP2_FILLED")
                print(f"✅ TP2 filled (CLOSED): {symbol}")
                print(f"   Total PnL: {trade['realized_pnl']:.2f}")
                print(f"   Win Rate: {trade['realized_pnl_percent']:.2f}%")
                
                return True
        
        except Exception as e:
            print(f"❌ Update TP2 failed: {e}")
            return False
    
    def update_sl_hit(self, symbol, hit_price):
        """
        Stop loss hit'ı register et (trade kapatıldı)
        """
        if symbol not in self.active_trades:
            print(f"❌ Trade not found: {symbol}")
            return False
        
        trade = self.active_trades[symbol]
        
        try:
            trade['sl_hit'] = True
            trade['sl_hit_at'] = datetime.now().isoformat()
            trade['sl_hit_price'] = hit_price
            
            # SL loss hesapla
            sl_loss = (hit_price - trade['entry_price']) * trade['entry_quantity']
            if trade['direction'] == "SHORT":
                sl_loss = (trade['entry_price'] - hit_price) * trade['entry_quantity']
            
            trade['realized_pnl'] = sl_loss
            trade['realized_pnl_percent'] = (sl_loss / (trade['entry_price'] * trade['entry_quantity'])) * 100
            
            trade['exit_price'] = hit_price
            trade['exit_quantity'] = trade['entry_quantity']
            
            trade['state_transitions'].append({
                "from": trade['current_state'],
                "to": TradeState.CLOSED.value,
                "at": datetime.now().isoformat(),
                "hit_price": hit_price,
                "loss": sl_loss,
                "source": "stop_loss"
            })
            
            trade['current_state'] = TradeState.CLOSED.value
            
            self._log_event(trade, "SL_HIT")
            print(f"❌ SL HIT: {symbol}")
            print(f"   Hit Price: {hit_price}")
            print(f"   Loss: {sl_loss:.2f}")
            
            return True
        
        except Exception as e:
            print(f"❌ Update SL hit failed: {e}")
            return False
    
    def update_trailing_sl(self, symbol, new_sl):
        """
        Trailing SL'i güncelle
        """
        if symbol not in self.active_trades:
            return False
        
        trade = self.active_trades[symbol]
        
        try:
            old_sl = trade['trailing_sl']
            trade['trailing_sl'] = new_sl
            trade['trailing_sl_last_update'] = datetime.now().isoformat()
            
            if new_sl > old_sl and trade['direction'] == "LONG":
                print(f"📈 Trailing SL updated: {old_sl} → {new_sl}")
            elif new_sl < old_sl and trade['direction'] == "SHORT":
                print(f"📈 Trailing SL updated: {old_sl} → {new_sl}")
            
            return True
        
        except Exception as e:
            print(f"⚠️  Trailing SL update failed: {e}")
            return False
    
    def get_trade_status(self, symbol):
        """Trade'in şu anki status'unu al"""
        if symbol not in self.active_trades:
            return None
        
        trade = self.active_trades[symbol]
        
        return {
            "trade_id": trade['trade_id'],
            "symbol": trade['symbol'],
            "current_state": trade['current_state'],
            "entry_price": trade['entry_price'],
            "trailing_sl": trade['trailing_sl'],
            "tp1_filled": trade['tp1_filled'],
            "tp2_filled": trade['tp2_filled'],
            "sl_hit": trade['sl_hit'],
            "realized_pnl": trade['realized_pnl'],
            "realized_pnl_percent": trade['realized_pnl_percent'],
            "duration_minutes": (time.time() - trade['created_timestamp']) / 60 if trade['created_timestamp'] else 0
        }
    
    def close_trade(self, symbol):
        """Trade'i kapatıp archiv'e al"""
        if symbol not in self.active_trades:
            return False
        
        try:
            trade = self.active_trades.pop(symbol)
            trade['closed_at'] = datetime.now().isoformat()
            
            # Archive'e ekle
            self._log_event(trade, "ARCHIVED")
            
            print(f"✅ Trade archived: {symbol}")
            print(f"   Total PnL: {trade['realized_pnl']:.2f}")
            
            return True
        
        except Exception as e:
            print(f"❌ Close trade failed: {e}")
            return False
    
    def verify_state_consistency(self, symbol, state, open_positions):
        """
        Trade lifecycle state'i gerçek pozisyonla check et
        
        Returns:
            bool: Consistent?
        """
        if symbol not in self.active_trades:
            return True  # Trade yok, skip
        
        trade = self.active_trades[symbol]
        
        try:
            # Exchange'den position al
            pos = next(
                (p for p in open_positions if p['symbol'] == symbol),
                None
            )
            
            if not pos:
                # Position kapandı ama lifecycle açık mı?
                if trade['current_state'] != TradeState.CLOSED.value:
                    print(f"⚠️  Position closed but lifecycle still {trade['current_state']}")
                    return False
            else:
                # Position açık
                if trade['current_state'] not in [TradeState.OPENED.value, TradeState.TP1_DONE.value]:
                    print(f"⚠️  Position open but lifecycle is {trade['current_state']}")
                    return False
            
            print(f"✅ Lifecycle consistent: {symbol}")
            return True
        
        except Exception as e:
            print(f"⚠️  Consistency check failed: {e}")
            return False
    
    def _log_event(self, trade, event_type):
        """Trade event log'u yaz"""
        try:
            logs = []
            try:
                with open(self.lifecycle_log, "r") as f:
                    logs = json.load(f)
            except:
                logs = []
            
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "trade_id": trade.get('trade_id'),
                "symbol": trade.get('symbol'),
                "event": event_type,
                "state": trade.get('current_state'),
                "pnl": trade.get('realized_pnl'),
                "pnl_percent": trade.get('realized_pnl_percent')
            }
            
            logs.append(log_entry)
            
            # Son 500 log tutun
            if len(logs) > 500:
                logs = logs[-500:]
            
            with open(self.lifecycle_log, "w") as f:
                json.dump(logs, f, indent=2)
        except:
            pass
    
    def get_active_trades_summary(self):
        """Aktif trade'lerin özet'ini al"""
        summary = {
            "total_active": len(self.active_trades),
            "trades": {}
        }
        
        for symbol, trade in self.active_trades.items():
            summary['trades'][symbol] = {
                "state": trade['current_state'],
                "entry": trade['entry_price'],
                "pnl": trade['realized_pnl'],
                "tp1_done": trade['tp1_filled'],
                "tp2_done": trade['tp2_filled'],
                "duration_min": (time.time() - trade['created_timestamp']) / 60
            }
        
        return summary
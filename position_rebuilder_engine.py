# ================= DETERMINISTIC POSITION REBUILDER =================
# Exchange'deki gerçek pozisyondan state'i yeniden oluştur

import json
import time
from datetime import datetime

class PositionRebuilder:
    """
    Exchange'deki pozisyondan deterministik şekilde state'i rebuild et
    
    Sorun:
    - State dosyası bozuldu
    - Ama exchange'de açık pozisyon var
    
    Çözüm:
    - Exchange'den gerçek pozisyon al
    - Entry price, SL, TP'leri hesapla
    - State'i rebuild et
    """
    
    def __init__(self, binance, state_manager):
        self.binance = binance
        self.state_manager = state_manager
        self.rebuild_log = "position_rebuild_log.json"
    
    def rebuild_position_state(self, symbol, direction, contracts, entry_price_estimate=None):
        """
        Exchange pozisyonundan state'i rebuild et
        
        Args:
            symbol: Trading pair (BTC/USDT)
            direction: LONG / SHORT
            contracts: Position size
            entry_price_estimate: Opsiyonel - trade history'den hesapla
            
        Returns:
            dict: Rebuilt state
        """
        print(f"\n🔄 REBUILDING STATE: {symbol} {direction} {contracts} contracts")
        
        try:
            # 1️⃣ Exchange'den trade history al
            try:
                trades = self.binance.fetch_my_trades(symbol, limit=50)
                if not trades:
                    print(f"⚠️  No trade history found for {symbol}")
                    return None
            except Exception as e:
                print(f"❌ Failed to fetch trade history: {e}")
                return None
            
            # 2️⃣ En yakın entry trade'i bul (aynı direction)
            recent_trades = [t for t in trades if t.get('info', {}).get('side') == direction.lower()]
            
            if not recent_trades:
                print(f"⚠️  No {direction} trades found")
                return None
            
            entry_trade = recent_trades[-1]  # Son entry trade
            entry_price = float(entry_trade.get('price', entry_price_estimate))
            entry_time = entry_trade.get('timestamp', int(time.time() * 1000))
            
            if not entry_price:
                print(f"❌ Could not determine entry price")
                return None
            
            print(f"✅ Found entry: {entry_price} at {datetime.fromtimestamp(entry_time/1000)}")
            
            # 3️⃣ En son trade'in fee'sini hesapla
            trade_fee = float(entry_trade.get('fee', {}).get('cost', 0))
            
            # 4️⃣ Current market price al
            try:
                ticker = self.binance.fetch_ticker(symbol)
                current_price = float(ticker['last'])
            except Exception as e:
                print(f"⚠️  Could not fetch current price: {e}")
                return None
            
            # 5️⃣ ATR hesapla (SL distance için)
            try:
                # 1 saat timeframe'den ATR al
                df = self.binance.fetch_ohlcv(symbol, '1h', limit=20)
                if df and len(df) >= 2:
                    closes = [candle[4] for candle in df]
                    highs = [candle[2] for candle in df]
                    lows = [candle[3] for candle in df]
                    
                    # TR hesapla
                    tr_list = []
                    for i in range(1, len(closes)):
                        tr = max(
                            highs[i] - lows[i],
                            abs(highs[i] - closes[i-1]),
                            abs(lows[i] - closes[i-1])
                        )
                        tr_list.append(tr)
                    
                    atr = sum(tr_list[-14:]) / len(tr_list[-14:]) if len(tr_list) >= 14 else sum(tr_list) / len(tr_list)
                else:
                    atr = entry_price * 0.02  # Default 2%
            except Exception as e:
                print(f"⚠️  ATR calculation failed: {e}")
                atr = entry_price * 0.02
            
            # 6️⃣ SL hesapla (entry'den 1.5 ATR uzak)
            if direction == "LONG":
                sl = entry_price - 1.5 * atr
                R = entry_price - sl
            else:
                sl = entry_price + 1.5 * atr
                R = sl - entry_price
            
            # 7️⃣ TP'leri belirle (R:2 ratio)
            tp1 = entry_price + R if direction == "LONG" else entry_price - R
            tp2 = entry_price + 2*R if direction == "LONG" else entry_price - 2*R
            
            # 8️⃣ Unrealized PnL hesapla
            if direction == "LONG":
                unrealized_pnl = (current_price - entry_price) * contracts
            else:
                unrealized_pnl = (entry_price - current_price) * contracts
            
            # 9️⃣ Rebuilt state oluştur
            rebuilt_state = {
                "peak": 10000.0,  # Bu mainten gelecek
                "entry": entry_price,
                "direction": direction,
                "sl": sl,
                "R": R,
                "risk_cut": False,
                "cooldown_until": 0,
                "tp1_done": False,
                "tp2_done": False,
                "trail_active": False,
                "entry_time": entry_time / 1000,  # timestamp to seconds
                "recovery_mode": True,  # ⚠️ Recovery mode işareti
                "entry_regime": None,
                "entry_risk": None,
                "entry_mtf_bias": None,
                "entry_latency_ms": 0,
                "highest_price": entry_price if direction == "LONG" else entry_price,
                "save_count": 0,
                "last_save": datetime.now().isoformat(),
                
                # ===== REBUILD METADATA =====
                "rebuilt_from_exchange": True,
                "rebuild_timestamp": datetime.now().isoformat(),
                "rebuild_source": "position_history",
                "exchange_entry_price": entry_price,
                "exchange_current_price": current_price,
                "exchange_unrealized_pnl": unrealized_pnl,
                "exchange_contracts": contracts,
                "calculated_atr": atr,
                "calculated_tp1": tp1,
                "calculated_tp2": tp2,
                "trade_history_length": len(recent_trades)
            }
            
            # 🔟 Log yaz
            self._log_rebuild({
                "timestamp": datetime.now().isoformat(),
                "symbol": symbol,
                "direction": direction,
                "entry_price": entry_price,
                "current_price": current_price,
                "sl": sl,
                "R": R,
                "unrealized_pnl": unrealized_pnl,
                "status": "SUCCESS"
            })
            
            print(f"✅ STATE REBUILD SUCCESSFUL")
            print(f"   Entry: {entry_price}")
            print(f"   SL: {sl}")
            print(f"   Current: {current_price}")
            print(f"   Unrealized PnL: {unrealized_pnl:.2f}")
            
            return rebuilt_state
        
        except Exception as e:
            print(f"❌ State rebuild failed: {e}")
            self._log_rebuild({
                "timestamp": datetime.now().isoformat(),
                "symbol": symbol,
                "error": str(e),
                "status": "FAILED"
            })
            return None
    
    def rebuild_from_exchange(self, binance, open_positions):
        """
        Açık pozisyonlardan state'i rebuild et
        
        Returns:
            dict: Rebuilt state veya None
        """
        if not open_positions or len(open_positions) == 0:
            print("⚠️  No open positions to rebuild")
            return None
        
        try:
            position = open_positions[0]
            symbol = position['symbol']
            contracts = float(position['contracts'])
            direction = "LONG" if contracts > 0 else "SHORT"
            
            # Entry price'ı tahmin et
            entry_price = float(position.get('info', {}).get('averagePrice', 0))
            
            rebuilt_state = self.rebuild_position_state(
                symbol, 
                direction, 
                abs(contracts),
                entry_price_estimate=entry_price
            )
            
            return rebuilt_state
        
        except Exception as e:
            print(f"❌ Exchange rebuild failed: {e}")
            return None
    
    def _log_rebuild(self, log_entry):
        """Rebuild log yaz"""
        try:
            logs = []
            try:
                with open(self.rebuild_log, "r") as f:
                    logs = json.load(f)
            except:
                logs = []
            
            logs.append(log_entry)
            
            # Son 100 log tutun
            if len(logs) > 100:
                logs = logs[-100:]
            
            with open(self.rebuild_log, "w") as f:
                json.dump(logs, f, indent=2)
        except:
            pass
    
    def verify_rebuild(self, rebuilt_state, open_positions):
        """
        Rebuild doğru mu kontrol et
        
        Returns:
            bool: Valid rebuild
        """
        if not rebuilt_state:
            return False
        
        try:
            # Entry price var mı?
            if not rebuilt_state.get("entry"):
                print("❌ Rebuilt state has no entry price")
                return False
            
            # SL var mı ve entry'den farklı mı?
            if not rebuilt_state.get("sl") or rebuilt_state["sl"] == rebuilt_state["entry"]:
                print("❌ Rebuilt state has invalid SL")
                return False
            
            # R (risk) hesaplanmış mı?
            if not rebuilt_state.get("R") or rebuilt_state["R"] <= 0:
                print("❌ Rebuilt state has invalid R")
                return False
            
            # Exchange pozisyonları kontrol et
            if open_positions:
                pos = open_positions[0]
                exchange_entry = float(pos.get('info', {}).get('averagePrice', 0))
                rebuilt_entry = rebuilt_state.get("entry", 0)
                
                # Entry price %1'den fazla farklı mı?
                price_diff = abs(exchange_entry - rebuilt_entry) / exchange_entry
                if price_diff > 0.01:  # %1 tolerance
                    print(f"⚠️  Entry price mismatch: exchange={exchange_entry}, rebuilt={rebuilt_entry}")
                    # Ama fail etme, warning ver
            
            print("✅ Rebuild verification PASSED")
            return True
        
        except Exception as e:
            print(f"❌ Rebuild verification failed: {e}")
            return False
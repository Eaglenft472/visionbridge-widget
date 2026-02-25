# ================= EXCHANGE-SIDE STOP ORDER ENGINE =================
import ccxt
import time

class ExchangeStopManager:
    """Binance Futures stop-loss order yönetimi"""
    
    def __init__(self):
        self.active_stops = {}
    
    def sync_with_exchange(self, binance, symbols):
        """Engine restart sonrası Exchange ile senkronize et"""
        print("\n🔄 Syncing stops with exchange...")
        self.active_stops.clear()
        synced_count = 0
        
        for symbol in symbols:
            try:
                open_orders = binance.fetch_open_orders(symbol)
                for order in open_orders:
                    order_type = str(order.get("type", "")).lower()
                    if "stop" in order_type:
                        stop_price = order.get("stopPrice") or order.get("info", {}).get("stopPrice")
                        self.active_stops[symbol] = {
                            "order_id": order["id"],
                            "stop_price": float(stop_price),
                            "timestamp": time.time(),
                            "synced": True
                        }
                        synced_count += 1
                        print(f"✅ Synced: {symbol} STOP @ {stop_price}")
            except:
                pass
        
        print(f"✅ Synced {synced_count} stops with exchange\n")
        return synced_count
    
    def place_stop_order(self, binance, symbol, direction, stop_price, quantity):
        """STOP_MARKET order yolla"""
        try:
            self.cancel_existing_stops(binance, symbol)
            
            side = "SELL" if direction.upper() == "LONG" else "BUY"
            
            params = {
                "stopPrice": float(round(float(stop_price), 6)),
                "reduceOnly": True,
                "workingType": "MARK_PRICE"
            }
            
            order = binance.create_order(
                symbol=symbol,
                type="STOP_MARKET",
                side=side,
                amount=float(quantity),
                price=None,
                params=params
            )
            
            self.active_stops[symbol] = {
                "order_id": order["id"],
                "stop_price": stop_price,
                "direction": direction,
                "quantity": quantity,
                "timestamp": time.time(),
                "side": side,
                "synced": False
            }
            
            print(f"✅ STOP order placed: {symbol} {direction} @ {stop_price}")
            return order
        
        except Exception as e:
            print(f"❌ STOP ORDER ERROR: {symbol} - {str(e)}")
            return None
    
    def cancel_existing_stops(self, binance, symbol):
        """Açık stop order'ları iptal et"""
        try:
            open_orders = binance.fetch_open_orders(symbol)
            cancelled_count = 0
            
            for order in open_orders:
                order_type = str(order.get("type", "")).lower()
                
                if "stop" in order_type or order_type == "stop_market":
                    try:
                        binance.cancel_order(order["id"], symbol)
                        cancelled_count += 1
                    except:
                        pass
            
            if symbol in self.active_stops:
                del self.active_stops[symbol]
            
            return True
        
        except Exception as e:
            print(f"❌ STOP CANCEL ERROR: {symbol} - {str(e)}")
            return False
    
    def update_stop_order(self, binance, symbol, direction, stop_price, quantity):
        """Stop order'ı güncelle"""
        try:
            positions = binance.fetch_positions([symbol])
            if positions:
                real_quantity = abs(float(positions[0].get("contracts", quantity)))
                quantity = real_quantity
        except:
            pass
        
        self.cancel_existing_stops(binance, symbol)
        time.sleep(0.5)
        return self.place_stop_order(binance, symbol, direction, stop_price, quantity)
    
    def get_active_stop(self, symbol):
        return self.active_stops.get(symbol)
    
    def print_all_stops(self):
        if self.active_stops:
            print("\n📊 Active STOP orders:")
            for sym, info in self.active_stops.items():
                print(f"  {sym}: @ {info['stop_price']}")
        else:
            print("ℹ️ No active stop orders")
    
    def get_active_stops_count(self):
        return len(self.active_stops)
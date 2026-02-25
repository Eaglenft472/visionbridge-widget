# ================= DYNAMIC MTF CACHE ENGINE =================
# Volatiliteye göre cache TTL'ı dinamik olarak ayarla

import time
from datetime import datetime

class DynamicMTFCache:
    """
    Multi-timeframe cache, dinamik TTL ile
    
    Logik:
    - Düşük volatilite (ATR < 0.5%): Cache 120 saniye
    - Normal volatilite (0.5%-1%): Cache 60 saniye
    - Yüksek volatilite (> 1%): Cache 30 saniye
    """
    
    def __init__(self, base_ttl=60):
        self.base_ttl = base_ttl
        self.cache = {}
        self.volatility_cache = {}
        
        # TTL boundaries
        self.ttl_low_volatility = 120      # %0.5 altında
        self.ttl_normal_volatility = 60    # %0.5-1% arası
        self.ttl_high_volatility = 30      # %1 üstünde
    
    def get_dynamic_ttl(self, symbol, atr_percent):
        """
        ATR yüzdesine göre dinamik TTL hesapla
        
        Args:
            symbol: Trading pair
            atr_percent: ATR as percentage (örn: 0.75)
            
        Returns:
            int: TTL in seconds
        """
        if atr_percent < 0.5:
            ttl = self.ttl_low_volatility
            volatility_level = "LOW"
        elif atr_percent < 1.0:
            ttl = self.ttl_normal_volatility
            volatility_level = "NORMAL"
        else:
            ttl = self.ttl_high_volatility
            volatility_level = "HIGH"
        
        self.volatility_cache[symbol] = {
            "atr_percent": atr_percent,
            "volatility_level": volatility_level,
            "ttl": ttl,
            "updated_at": time.time()
        }
        
        return ttl
    
    def set_cache(self, symbol, timeframe, data, ttl=None):
        """
        Cache'e veri ekle (TTL ile)
        
        Args:
            symbol: Trading pair
            timeframe: 1m, 5m, 15m, 1h
            data: DataFrame veya dict
            ttl: Custom TTL (opsiyonel)
        """
        if symbol not in self.cache:
            self.cache[symbol] = {}
        
        self.cache[symbol][timeframe] = {
            "data": data,
            "cached_at": time.time(),
            "ttl": ttl or self.base_ttl
        }
    
    def get_cache(self, symbol, timeframe):
        """
        Cache'den veri al (eğer valid ise)
        
        Returns:
            data veya None (expired ise)
        """
        if symbol not in self.cache or timeframe not in self.cache[symbol]:
            return None
        
        cached_entry = self.cache[symbol][timeframe]
        age = time.time() - cached_entry["cached_at"]
        ttl = cached_entry["ttl"]
        
        if age > ttl:
            # Expired - sil ve None döndür
            del self.cache[symbol][timeframe]
            return None
        
        return cached_entry["data"]
    
    def get_cache_status(self, symbol):
        """Symbol için cache status'unu al"""
        if symbol not in self.cache:
            return None
        
        status = {
            "symbol": symbol,
            "timeframes_cached": list(self.cache[symbol].keys()),
            "volatility": self.volatility_cache.get(symbol),
            "entries": {}
        }
        
        for timeframe, entry in self.cache[symbol].items():
            age = time.time() - entry["cached_at"]
            ttl = entry["ttl"]
            is_valid = age < ttl
            
            status["entries"][timeframe] = {
                "age_seconds": age,
                "ttl_seconds": ttl,
                "valid": is_valid,
                "expires_in": ttl - age
            }
        
        return status
    
    def clear_expired(self, symbol=None):
        """Expired cache'leri sil"""
        try:
            if symbol:
                # Specific symbol
                if symbol in self.cache:
                    expired = []
                    for tf, entry in self.cache[symbol].items():
                        age = time.time() - entry["cached_at"]
                        if age > entry["ttl"]:
                            expired.append(tf)
                    
                    for tf in expired:
                        del self.cache[symbol][tf]
                    
                    return len(expired)
            else:
                # All symbols
                total_cleared = 0
                for symbol in list(self.cache.keys()):
                    total_cleared += self.clear_expired(symbol)
                
                return total_cleared
        except Exception as e:
            print(f"⚠️  Cache clear failed: {e}")
            return 0
    
    def get_cache_efficiency(self):
        """Cache efficiency metrikleri al"""
        total_entries = 0
        total_age = 0
        
        for symbol in self.cache:
            for timeframe, entry in self.cache[symbol].items():
                total_entries += 1
                age = time.time() - entry["cached_at"]
                total_age += age
        
        if total_entries == 0:
            return {
                "total_entries": 0,
                "average_age_seconds": 0,
                "symbols_cached": 0
            }
        
        return {
            "total_entries": total_entries,
            "average_age_seconds": total_age / total_entries,
            "symbols_cached": len(self.cache)
        }
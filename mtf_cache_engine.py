# ================= MTF CACHE ENGINE =================
import time

class MTFCache:
    def __init__(self, cache_ttl_seconds=60):
        self.cache = {}
        self.ttl = cache_ttl_seconds
    
    def get_or_fetch(self, symbol, timeframe, fetch_func):
        """Cache varsa döndür, yoksa fetch et"""
        key = f"{symbol}:{timeframe}"
        now = time.time()
        
        if key in self.cache:
            cached_df, timestamp = self.cache[key]
            age = now - timestamp
            
            if age < self.ttl:
                return cached_df
        
        try:
            df = fetch_func(symbol, timeframe)
            self.cache[key] = (df, now)
            return df
        except:
            if key in self.cache:
                return self.cache[key][0]
            return None
    
    def clear_expired(self):
        """Eski cache'leri temizle"""
        now = time.time()
        expired = [k for k, (_, ts) in self.cache.items() if now - ts > self.ttl * 2]
        for k in expired:
            del self.cache[k]
        if expired:
            print(f"🧹 Cleared {len(expired)} expired cache entries")
# ================= CORRELATION RISK ENGINE =================
import numpy as np
import time

class CorrelationEngine:
    def __init__(self, lookback=200, corr_threshold=0.75):
        self.lookback = lookback
        self.corr_threshold = corr_threshold
        self.corr_cache = {}
        self.cache_ttl = 60
    
    def calculate_returns(self, df):
        """Log returns hesapla"""
        if df is None or len(df) < 2:
            return None
        close_prices = df["close"].iloc[-self.lookback:]
        returns = np.log(close_prices.pct_change().dropna())
        return returns
    
    def correlation_between(self, symbol_a, symbol_b, df_a, df_b):
        """İki sembol arasında korelasyon"""
        try:
            pair = tuple(sorted([symbol_a, symbol_b]))
            if pair in self.corr_cache:
                corr_val, ts = self.corr_cache[pair]
                if time.time() - ts < self.cache_ttl:
                    return corr_val
            
            ret_a = self.calculate_returns(df_a)
            ret_b = self.calculate_returns(df_b)
            
            if ret_a is None or ret_b is None:
                return 0.0
            
            min_len = min(len(ret_a), len(ret_b))
            ret_a = ret_a.iloc[-min_len:]
            ret_b = ret_b.iloc[-min_len:]
            
            corr = np.corrcoef(ret_a, ret_b)[0, 1]
            corr_val = abs(float(corr)) if not np.isnan(corr) else 0.0
            
            self.corr_cache[pair] = (corr_val, time.time())
            
            return corr_val
        except:
            return 0.0
    
    def check_correlation_risk(self, open_positions, new_symbol, new_df, dataframes_dict):
        """Korelasyon riskini kontrol et"""
        if not open_positions:
            return "pass", 0.0
        
        max_corr = 0.0
        
        for pos in open_positions:
            symbol = pos["symbol"].replace("USDT", "/USDT")
            
            df_existing = dataframes_dict.get(symbol)
            if df_existing is None:
                continue
            
            corr = self.correlation_between(symbol, new_symbol, df_existing, new_df)
            max_corr = max(max_corr, corr)
        
        if max_corr > self.corr_threshold:
            return "reduce", max_corr
        elif max_corr > 0.65:
            return "reduce", max_corr
        else:
            return "pass", max_corr
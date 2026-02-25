# ================= SMART TRAILING STOP ENGINE =================
import numpy as np

def compute_smart_trailing_stop(price, entry, direction, atr, lookback=10, 
                                sensitivity=0.7, activation_ratio=1.5, df=None):
    """Akıllı trailing stop hesapla"""
    if direction == "LONG":
        profit = price - entry
        activation_level = atr * activation_ratio
        
        if profit > activation_level:
            if df is not None and len(df) >= lookback:
                recent_low = df.iloc[-lookback:]["low"].min()
                trail_distance = (price - recent_low) * sensitivity
                new_sl = price - trail_distance
                return max(new_sl, entry - atr)
            else:
                trail_distance = atr * sensitivity
                return price - trail_distance
    else:
        profit = entry - price
        activation_level = atr * activation_ratio
        
        if profit > activation_level:
            if df is not None and len(df) >= lookback:
                recent_high = df.iloc[-lookback:]["high"].max()
                trail_distance = (recent_high - price) * sensitivity
                new_sl = price + trail_distance
                return min(new_sl, entry + atr)
            else:
                trail_distance = atr * sensitivity
                return price + trail_distance
    return None

def get_trailing_stats(df, direction, lookback=20):
    """Trailing istatistikleri"""
    if len(df) < lookback:
        return None
    if direction == "LONG":
        recent_low = df.iloc[-lookback:]["low"].min()
        current_high = df.iloc[-1]["high"]
        volatility = current_high - recent_low
    else:
        recent_high = df.iloc[-lookback:]["high"].max()
        current_low = df.iloc[-1]["low"]
        volatility = recent_high - current_low
    return {"volatility": volatility, "lookback": lookback}
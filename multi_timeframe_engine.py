# ================= MULTI-TIMEFRAME BIAS ENGINE =================
import numpy as np

def analyze_multi_timeframe_bias(symbol, timeframes, weights, direction):
    """Çoklu zaman dilimi sapması analizi"""
    bias_scores = []
    total_weight = sum(weights.values())
    
    for tf in timeframes:
        try:
            score = 0.7 if direction == "LONG" else 0.6
            weight = weights.get(tf, 0.25) / total_weight
            bias_scores.append(score * weight)
        except:
            continue
    
    return sum(bias_scores) if bias_scores else 0.5

def get_mtf_alignment(symbol, timeframes):
    """Tüm zaman dilimlerinin hizalaması"""
    return 0.5
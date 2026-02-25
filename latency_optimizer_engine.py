# ================= EXECUTION LATENCY OPTIMIZER =================
import numpy as np
from collections import deque

class LatencyOptimizer:
    def __init__(self, max_history=100, threshold_ms=100):
        self.latency_history = deque(maxlen=max_history)
        self.threshold_ms = threshold_ms
        self.optimization_level = 1
    
    def record_latency(self, latency_ms):
        """İşlem gecikmesi kaydı"""
        self.latency_history.append(latency_ms)
        self._adjust_optimization()
    
    def _adjust_optimization(self):
        """Optimizasyon seviyesi ayarla"""
        if len(self.latency_history) < 10:
            return
        avg_latency = np.mean(list(self.latency_history))
        if avg_latency > self.threshold_ms * 2:
            self.optimization_level = 3
        elif avg_latency > self.threshold_ms:
            self.optimization_level = 2
        else:
            self.optimization_level = 1
    
    def get_optimization_params(self):
        """Optimizasyon parametrelerini al"""
        params = {
            1: {"batch_size": 5, "timeout": 30, "retry_count": 2},
            2: {"batch_size": 3, "timeout": 20, "retry_count": 3},
            3: {"batch_size": 1, "timeout": 10, "retry_count": 4}
        }
        return params.get(self.optimization_level, params[1])
    
    def get_stats(self):
        """Latency istatistikleri"""
        if not self.latency_history:
            return {}
        return {
            "avg_ms": np.mean(list(self.latency_history)),
            "max_ms": np.max(list(self.latency_history)),
            "min_ms": np.min(list(self.latency_history)),
            "p95_ms": np.percentile(list(self.latency_history), 95),
            "optimization_level": self.optimization_level
        }

def optimize_execution_latency(order_params, current_latency_ms, threshold_ms=100):
    """İşlem gecikmesini optimize et"""
    optimization_factor = max(1.0, threshold_ms / current_latency_ms)
    return {
        "use_fast_api": optimization_factor > 1.2,
        "priority": "high" if optimization_factor > 1.5 else "normal",
        "batch": "single" if optimization_factor > 1.8 else "batch",
        "timeout_reduction": min(0.5, 1.0 / optimization_factor)
    }
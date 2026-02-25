# ================= EXECUTION RESILIENCE ENGINE =================
import time

class ExecutionResilient:
    def __init__(self, max_retries=3, slippage_threshold=0.002, retry_delay=2):
        self.max_retries = max_retries
        self.slippage_threshold = slippage_threshold
        self.retry_delay = retry_delay
    
    def execute_with_retry(self, binance, symbol, direction, qty, safe_market_order_func):
        """safe_market_order'ı 3 kez dene - LATENCY ÖLÇÜLÜ"""
        
        exec_start_time = time.time()
        expected_price = binance.fetch_ticker(symbol)["last"]
        
        for attempt in range(self.max_retries):
            try:
                success = safe_market_order_func(binance, symbol, direction, qty)
                
                if not success:
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                    continue
                
                time.sleep(1)
                filled_order = binance.fetch_last_trade(symbol)
                
                if filled_order:
                    filled_price = filled_order["price"]
                    slippage = abs(filled_price - expected_price) / expected_price
                else:
                    slippage = 0.0
                
                exec_latency = (time.time() - exec_start_time) * 1000
                return True, slippage, exec_latency
            
            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
        
        exec_latency = (time.time() - exec_start_time) * 1000
        return False, 0.0, exec_latency
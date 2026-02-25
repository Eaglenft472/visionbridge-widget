import ccxt
import pandas as pd
import time
from config import MOCK_MODE, MOCK_INITIAL_BALANCE, TIMEFRAME

if MOCK_MODE:
    # Mock Binance client
    class MockBinance:
        def __init__(self):
            self.balance = {
                'USDT': {'free': MOCK_INITIAL_BALANCE, 'used': 0, 'total': MOCK_INITIAL_BALANCE},
                'BTC': {'free': 0, 'used': 0, 'total': 0},
                'ETH': {'free': 0, 'used': 0, 'total': 0},
            }
            self.positions = []
            self.orders = []
            self.mock_price = 40000
            self.trade_count = 0
        
        def fetch_balance(self):
            return {
                'USDT': self.balance.get('USDT', {'free': MOCK_INITIAL_BALANCE, 'used': 0, 'total': MOCK_INITIAL_BALANCE}),
                'total': {'USDT': self.balance['USDT']['total']},
                'free': {'USDT': self.balance['USDT']['free']}
            }
        
        def fetch_positions(self, symbols=None):
            # Simulate 1 open position
            if self.trade_count > 0:
                return [{
                    'symbol': 'BTC/USDT',
                    'contracts': 0.05,
                    'contractSize': 1,
                    'side': 'long',
                    'unrealizedPnl': 100,
                    'percentage': 0.01,
                    'markPrice': self.mock_price,
                    'liquidationPrice': 30000,
                    'collateral': 2000,
                    'markValue': 2000,
                    'notional': 2000,
                    'info': {
                        'averagePrice': 40000,
                        'markPrice': self.mock_price,
                        'positionAmt': '0.05',
                        'unrealizedProfit': '100'
                    }
                }]
            return []
        
        def fetch_ticker(self, symbol):
            import random
            self.mock_price += random.uniform(-10, 10)
            return {
                'symbol': symbol,
                'last': self.mock_price,
                'bid': self.mock_price - 1,
                'ask': self.mock_price + 1,
                'high': self.mock_price + 100,
                'low': self.mock_price - 100
            }
        
        def create_market_order(self, symbol, side, amount, params=None):
            self.trade_count += 1
            return {
                'id': f'mock_{self.trade_count}',
                'status': 'closed',
                'symbol': symbol,
                'side': side,
                'amount': amount,
                'price': self.mock_price
            }
        
        def create_market_buy_order(self, symbol, amount, params=None):
            """Buy order"""
            self.trade_count += 1
            return {
                'id': f'mock_{self.trade_count}',
                'status': 'closed',
                'symbol': symbol,
                'side': 'buy',
                'amount': amount,
                'price': self.mock_price
            }
        
        def create_market_sell_order(self, symbol, amount, params=None):
            """Sell order"""
            self.trade_count += 1
            return {
                'id': f'mock_{self.trade_count}',
                'status': 'closed',
                'symbol': symbol,
                'side': 'sell',
                'amount': amount,
                'price': self.mock_price
            }
        
        def fapiPrivatePostLeverage(self, params=None):
            """Set leverage"""
            return {'leverage': 5, 'maxNotionalValue': 100000}
        
        def fetch_ohlcv(self, symbol, timeframe, limit=100):
            import random
            # Generate realistic OHLCV data
            ohlcv = []
            price = 40000
            timestamp = int(time.time() * 1000) - (limit * 5 * 60 * 1000)  # 5m candles
            
            for i in range(limit):
                price += random.uniform(-50, 50)
                open_p = price
                close_p = price + random.uniform(-30, 30)
                high_p = max(open_p, close_p) + random.uniform(0, 20)
                low_p = min(open_p, close_p) - random.uniform(0, 20)
                volume = random.uniform(100, 1000)
                
                ohlcv.append([timestamp, open_p, high_p, low_p, close_p, volume])
                timestamp += 5 * 60 * 1000  # 5m
            
            return ohlcv
        
        def amount_to_precision(self, symbol, amount):
            """Round amount to exchange precision"""
            return round(amount, 4)

        def price_to_precision(self, symbol, price):
            """Round price to exchange precision"""
            return round(price, 2)

        def cost_to_precision(self, symbol, cost):
            """Round cost to exchange precision"""
            return round(cost, 2)
    
    binance = MockBinance()
    print("��� MOCK MODE ENABLED - No real trades!")
else:
    binance = ccxt.binance({
        'apiKey': 'YOUR_API_KEY',
        'secret': 'YOUR_API_SECRET',
    })

# ================= INDICATORS =================

def ema(series, length):
    return series.ewm(span=length, adjust=False).mean()

def rsi(series, length=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(length).mean()
    avg_loss = loss.rolling(length).mean()

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def atr(high, low, close, length=14):
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(length).mean()

def adx(high, low, close, length=14):
    plus_dm = high.diff()
    minus_dm = low.diff()

    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm > 0] = 0

    tr = atr(high, low, close, length)

    plus_di = 100 * (plus_dm.rolling(length).mean() / tr)
    minus_di = 100 * (minus_dm.abs().rolling(length).mean() / tr)

    dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
    return dx.rolling(length).mean()

def macd(series, fast=12, slow=26, signal=9):
    ema_fast = ema(series, fast)
    ema_slow = ema(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = ema(macd_line, signal)
    return macd_line, signal_line

# ================= DATA FETCH =================

def fetch_dataframe(symbol):
    try:
        raw_data = binance.fetch_ohlcv(symbol, TIMEFRAME, limit=500)

        df = pd.DataFrame(
            raw_data,
            columns=["timestamp", "open", "high", "low", "close", "volume"]
        )

        df["t"] = pd.to_datetime(df["timestamp"], unit="ms")

        # EMA
        df["ema20"] = ema(df["close"], 20)
        df["ema50"] = ema(df["close"], 50)
        df["ema200"] = ema(df["close"], 200)

        # RSI
        df["rsi"] = rsi(df["close"], 14)

        # MACD
        macd_line, signal_line = macd(df["close"])
        df["macd"] = macd_line
        df["macds"] = signal_line

        # ATR
        df["atr"] = atr(df["high"], df["low"], df["close"], 14)

        # ADX
        df["adx"] = adx(df["high"], df["low"], df["close"], 14)

        # Volume average
        df["vol_avg"] = df["volume"].rolling(20).mean()

        df = df.dropna().reset_index(drop=True)

        return df

    except Exception as e:
        print(f"❌ Data Fetch Error ({symbol}): {e}")
        return None
from data_engine import binance
from config import LEVERAGE

def calculate_size(symbol, equity, entry, sl, risk):
    try:
        risk_amount = equity * risk
        R = abs(entry - sl)

        if R == 0:
            return 0

        # Birim bazında miktar (Örn: Kaç adet BTC?)
        amount = risk_amount / R
        
        # Binance hassasiyetine çevir
        precision_amount = float(binance.amount_to_precision(symbol, amount))
        
        # --- Minimum Tutar Kontrolü ---
        # Futures'ta genelde 5-10 USDT altı emirler reddedilir
        notional_value = precision_amount * entry
        if notional_value < 10: # Minimum 10 USDT kuralı
            print(f"⚠️ {symbol} için hesaplanan tutar çok düşük: {notional_value} USDT")
            return 0
            
        return precision_amount
    except Exception as e:
        print(f"❌ Size Calculation Error: {e}")
        return 0

def set_leverage(symbol):
    try:
        # Binance sembol formatı (BTC/USDT -> BTCUSDT)
        formatted_symbol = symbol.replace("/", "").replace(":", "")
        
        # Kaldıraç ayarla
        binance.fapiPrivatePostLeverage({
            "symbol": formatted_symbol,
            "leverage": LEVERAGE
        })
        
        # Opsiyonel: Marjin tipini ISOLATED olarak ayarla (Daha güvenli)
        try:
            binance.fapiPrivatePostMarginType({
                "symbol": formatted_symbol,
                "marginType": "ISOLATED"
            })
        except:
            pass # Zaten o moddaysa hata verebilir, geçiyoruz
            
    except Exception as e:
        print(f"⚠️ Leverage/Margin Set Error ({symbol}): {e}")
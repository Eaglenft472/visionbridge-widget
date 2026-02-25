def detect_trend(df):
    """
    Market Structure (Asıl Temel) ve EMA hibrit trend analizi.
    HH/HL (BOS) + EMA dizilimi ile en kaliteli yönü bulur.
    """
    if len(df) < 50: return None

    last = df.iloc[-1]
    prev = df.iloc[-2]
    
    # 1. Zirve ve Dip Takibi (Basit HH/LL Kontrolü)
    recent_highs = df["high"].iloc[-20:-1].max()
    recent_lows = df["low"].iloc[-20:-1].min()
    
    # --- BULLISH STRUCTURE (BOS) ---
    # Fiyat son 20 mumun zirvesini kırdıysa (BOS) ve EMA'lar destekliyorsa
    is_bullish_bos = last["close"] > recent_highs
    is_ema_bullish = last["ema20"] > last["ema50"]
    
    # --- BEARISH STRUCTURE (BOS) ---
    # Fiyat son 20 mumun dibini kırdıysa (BOS) ve EMA'lar destekliyorsa
    is_bearish_bos = last["close"] < recent_lows
    is_ema_bearish = last["ema20"] < last["ema50"]

    # 2. KARAR MEKANİZMASI
    # Strong Long: Hem EMA dizilimi mükemmel hem de BOS (Zirve Kırılımı) var
    if is_bullish_bos and last["ema20"] > last["ema50"] > last["ema200"]:
        return "STRONG_LONG"
    
    # Strong Short: Hem EMA dizilimi mükemmel hem de BOS (Dip Kırılımı) var
    elif is_bearish_bos and last["ema20"] < last["ema50"] < last["ema200"]:
        return "STRONG_SHORT"
    
    # Normal Trend: Sadece EMA dizilimi yeterli
    elif is_ema_bullish:
        return "LONG"
    
    elif is_ema_bearish:
        return "SHORT"
    
    return "NEUTRAL"
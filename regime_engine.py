def detect_regime(df):
    """
    ADX ve EMA dizilimi kullanarak piyasa rejimini belirler.
    TREND: Güçlü ve yönlü hareket.
    RANGE: Yatay ve kararsız yapı.
    NORMAL: Geçiş evresi.
    """
    last = df.iloc[-1]
    adx = last["adx"]
    
    # EMA dizilimi (Asıl Temel Trend Teyidi)
    # EMA'lar birbirinden uzaklaşıyorsa trend genişliyor demektir.
    ema_spread = abs(last["ema20"] - last["ema50"]) / last["ema50"]

    # 1. GÜÇLÜ TREND (Vites 5)
    if adx > 25 and ema_spread > 0.005: # %0.5'lik bir açılma payı
        return "TREND"
    
    # 2. RANGE / YATAY (Vites Boşta)
    # ADX düşükse ve EMA'lar birbirine çok yakınsa/birbirine girmişse
    elif adx < 18 or ema_spread < 0.002:
        return "RANGE"
    
    # 3. NORMAL / GEÇİŞ (Vites 2-3)
    else:
        return "NORMAL"
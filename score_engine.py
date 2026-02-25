def compute_score(df):
    """
    Enterprise v4 Skor Motoru.
    İndikatörleri önem sırasına göre ağırlıklandırır.
    """
    last = df.iloc[-1]
    score = 0

    # 1. TREND GÜCÜ (Kritik - 0.3)
    # ADX 20-25 arası zayıf, 25+ güçlü trenddir.
    if last["adx"] > 25:
        score += 0.3
    elif last["adx"] > 20:
        score += 0.15

    # 2. HAREKETLİ ORTALAMA DİZİLİMİ (Trend Yönü - 0.2)
    # EMA 20'nin 50 üzerinde olması orta vade trend teyididir.
    if last["ema20"] > last["ema50"]:
        score += 0.2

    # 3. HACİM VE KURUMSAL İLGİ (Kritik - 0.3)
    # Vol_avg üzerindeki %30'luk artış, BOS'u destekleyen 'smart money' kanıtıdır.
    if last["volume"] > last["vol_avg"] * 1.3:
        score += 0.3
    elif last["volume"] > last["vol_avg"]:
        score += 0.1

    # 4. MOMENTUM (Destekleyici - 0.1)
    # MACD kesisimi momentumun yönünü teyit eder.
    if last["macd"] > last["macds"]:
        score += 0.1

    # 5. RSI BÖLGESİ (Onay - 0.1)
    # 50 üzerindeki RSI, boğaların kontrolü ele aldığını gösterir.
    if last["rsi"] > 50:
        score += 0.1

    # Not: Pattern Engine'den gelecek +0.15 puan ile 
    # Diamond Setup (1.0+) puanına ulaşmak artık mümkün.
    
    return round(score, 2)
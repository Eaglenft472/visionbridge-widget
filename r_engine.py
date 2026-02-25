# r_engine.py içeriği
def dynamic_R_multiplier(df, score):
    """Trend gücüne (ADX) ve MS skoruna göre R katsayısını belirler."""
    adx = df.iloc[-1].get("adx", 25)
    base = 2.0
    if adx > 30: base += 0.5    # Güçlü trend: Daha geniş stop
    if score > 0.9: base += 0.5  # Çok güvenli setup
    if adx < 20: base -= 0.5    # Zayıf trend: Daha dar stop
    return max(base, 1.2)
def frequency_gate(df):

    atr = df.iloc[-1]["atr"]
    atr_prev = df.iloc[-5]["atr"]

    # Vol expansion
    if atr > atr_prev * 1.1:
        return 0.8   # daha sık trade

    # Vol contraction
    if atr < atr_prev * 0.9:
        return 1.2   # daha seçici

    return 1.0
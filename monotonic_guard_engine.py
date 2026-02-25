# ================= SL MONOTONIC GUARD ENGINE =================

def monotonic_sl_guard(old_sl, new_sl, direction):
    """SL asla geriye gitmemeli"""
    if direction == "LONG":
        return max(old_sl, new_sl)
    else:
        return min(old_sl, new_sl)

def validate_sl_movement(old_sl, new_sl, direction, max_move_percent=0.5):
    """SL hareket kontrolü"""
    if old_sl is None:
        return new_sl
    allowed_move = old_sl * (max_move_percent / 100)
    if direction == "LONG":
        return min(new_sl, old_sl + allowed_move)
    else:
        return max(new_sl, old_sl - allowed_move)
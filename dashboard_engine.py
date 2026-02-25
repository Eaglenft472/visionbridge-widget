import requests

TELEGRAM_TOKEN = '8763094320:AAGSq3tXa6JWLsdYc40wqi9Xr4oMloPGuMU'
TELEGRAM_CHAT_ID = '6350700231'


def telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": msg,
            "parse_mode": "Markdown"
        }, timeout=10)
    except:
        pass


def send_dashboard(
    equity,
    peak,
    dd,
    best_symbol=None,
    best_score=None,
    threshold=None,
    mode=None,
    telegram_func=None
):
    """
    Main.py ile uyumlu sade dashboard.
    """

    dd_percent = round(dd * 100, 2)

    msg = f"""
🏛 *HYBRID FUND ENGINE*

💰 Equity: `{round(equity,2)}`
📈 Peak: `{round(peak,2)}`
📉 DD: `{dd_percent}%`

🎯 Best Coin: `{best_symbol if best_symbol else '-'}`  
Score: `{best_score if best_score else '-'}`  
Threshold: `{threshold if threshold else '-'}`  
Mode: `{mode if mode else '-'}`

🕒 System Running...
"""

    if telegram_func:
        telegram_func(msg)
    else:
        telegram(msg)
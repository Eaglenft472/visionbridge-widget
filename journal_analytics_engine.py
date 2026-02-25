# ================= TRADE JOURNAL ANALYTICS ENGINE =================
import json
import os
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np

def record_trade_journal(trade_data, journal_path="trade_journal.json"):
    """İşlem defterine kaydı"""
    journal = []
    if os.path.exists(journal_path):
        try:
            with open(journal_path, "r") as f:
                journal = json.load(f)
        except:
            journal = []
    journal.append(trade_data)
    with open(journal_path, "w") as f:
        json.dump(journal[-1000:], f, indent=2)

def close_trade_journal(exit_price, exit_reason, journal_path="trade_journal.json"):
    """Son işlemi kapat"""
    if not os.path.exists(journal_path):
        return
    try:
        with open(journal_path, "r") as f:
            journal = json.load(f)
        if journal:
            last_trade = journal[-1]
            last_trade["exit_price"] = exit_price
            last_trade["exit_reason"] = exit_reason
            last_trade["exit_time"] = datetime.now().isoformat()
            last_trade["hold_time_minutes"] = (
                (datetime.fromisoformat(last_trade["exit_time"]) - 
                 datetime.fromisoformat(last_trade["timestamp"])).total_seconds() / 60
            )
            if last_trade["direction"] == "LONG":
                pnl_pct = ((exit_price - last_trade["entry_price"]) / last_trade["entry_price"] * 100)
            else:
                pnl_pct = ((last_trade["entry_price"] - exit_price) / last_trade["entry_price"] * 100)
            last_trade["pnl_percent"] = pnl_pct
            with open(journal_path, "w") as f:
                json.dump(journal, f, indent=2)
    except:
        pass

def analyze_journal_metrics(journal_path="trade_journal.json"):
    """Günlük metriklerini analiz et"""
    if not os.path.exists(journal_path):
        return {"total_trades": 0, "win_rate": 0, "avg_hold_time": 0, "avg_pnl_percent": 0}
    try:
        with open(journal_path, "r") as f:
            journal = json.load(f)
        if not journal:
            return {"total_trades": 0, "win_rate": 0, "avg_hold_time": 0}
        closed_trades = [t for t in journal if "exit_price" in t]
        if not closed_trades:
            return {"total_trades": len(journal), "win_rate": 0, "avg_hold_time": 0, "open_trades": len(journal)}
        pnl_values = [t.get("pnl_percent", 0) for t in closed_trades]
        hold_times = [t.get("hold_time_minutes", 0) for t in closed_trades]
        wins = len([p for p in pnl_values if p > 0])
        return {
            "total_trades": len(journal),
            "closed_trades": len(closed_trades),
            "open_trades": len(journal) - len(closed_trades),
            "win_rate": (wins / len(closed_trades) * 100) if closed_trades else 0,
            "avg_hold_time": np.mean(hold_times) if hold_times else 0,
            "avg_pnl_percent": np.mean(pnl_values) if pnl_values else 0,
            "best_trade": max(pnl_values) if pnl_values else 0,
            "worst_trade": min(pnl_values) if pnl_values else 0,
        }
    except:
        return {}

def get_journal_summary(days=7, journal_path="trade_journal.json"):
    """Son N günün özeti"""
    if not os.path.exists(journal_path):
        return {}
    try:
        with open(journal_path, "r") as f:
            journal = json.load(f)
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_trades = [t for t in journal if datetime.fromisoformat(t["timestamp"]) > cutoff_date]
        closed_recent = [t for t in recent_trades if "exit_price" in t]
        pnl_values = [t.get("pnl_percent", 0) for t in closed_recent]
        return {
            "period_days": days,
            "total_trades": len(recent_trades),
            "closed_trades": len(closed_recent),
            "win_rate": (len([p for p in pnl_values if p > 0]) / len(closed_recent) * 100) if closed_recent else 0,
            "total_pnl_percent": sum(pnl_values),
            "avg_pnl_percent": np.mean(pnl_values) if pnl_values else 0
        }
    except:
        return {}
# ================= TELEGRAM DASHBOARD ENGINE =================
# Rich, detailed, formatted Telegram notifications

import requests
import json
from datetime import datetime
import traceback

class TelegramDashboard:
    """
    Advanced Telegram dashboard with rich formatting
    
    Featureler:
    - Startup/Shutdown bilgisi
    - Real-time metrikleri
    - Error detayları
    - Trade açılışı/kapanışı
    - Watchdog status
    - Performance metrikleri
    """
    
    def __init__(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{self.token}"
        
        # Rate limiting (max 30 msg/sec)
        self.last_send = {}
        self.min_interval = 0.1  # Saniye
    
    def send_message(self, text, parse_mode="HTML"):
        """
        Mesaj gönder
        
        Args:
            text: Mesaj içeriği (HTML formatlanabilir)
            parse_mode: HTML veya Markdown
        """
        try:
            payload = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": parse_mode
            }
            
            response = requests.post(
                f"{self.api_url}/sendMessage",
                json=payload,
                timeout=10
            )
            
            return response.status_code == 200
        
        except Exception as e:
            print(f"⚠️  Telegram send failed: {e}")
            return False
    
    def startup_notification(self, engine_version, status_dict):
        """
        Sistem başlatıldığında çalıştır
        
        Args:
            engine_version: Engine versiyonu (örn: "v8.1")
            status_dict: Status bilgisi dict
        """
        message = f"""
🚀 <b>ENGINE STARTED</b> 🚀

<b>Version:</b> {engine_version}
<b>Started At:</b> {datetime.now().strftime('%H:%M:%S')}
<b>Date:</b> {datetime.now().strftime('%d.%m.%Y')}

<b>📊 SYSTEM STATUS:</b>
"""
        
        # Risk architecture
        if status_dict.get("risk_architecture"):
            message += "\n<b>Risk Architecture:</b>\n"
            for engine, status in status_dict["risk_architecture"].items():
                emoji = "✅" if status else "❌"
                message += f"{emoji} {engine}\n"
        
        # Institutional engines
        if status_dict.get("institutional_engines"):
            message += "\n<b>Institutional Engines:</b>\n"
            for engine, status in status_dict["institutional_engines"].items():
                emoji = "✅" if status else "❌"
                message += f"{emoji} {engine}\n"
        
        message += f"\n<b>Initial Equity:</b> ${status_dict.get('initial_equity', 'N/A'):.2f}"
        message += f"\n<b>Max Positions:</b> {status_dict.get('max_positions', 'N/A')}"
        
        self.send_message(message)
    
    def shutdown_notification(self, reason="Manual shutdown", stats=None):
        """
        Sistem kapandığında çalıştır
        
        Args:
            reason: Neden kapatıldığı
            stats: Son istatistikler
        """
        message = f"""
🛑 <b>ENGINE STOPPED</b> 🛑

<b>Reason:</b> {reason}
<b>Stopped At:</b> {datetime.now().strftime('%H:%M:%S')}

"""
        
        if stats:
            message += "<b>📊 FINAL STATISTICS:</b>\n"
            message += f"<b>Final Equity:</b> ${stats.get('final_equity', 'N/A'):.2f}\n"
            message += f"<b>Total Return:</b> {stats.get('total_return', 'N/A')}%\n"
            message += f"<b>Total Trades:</b> {stats.get('total_trades', 'N/A')}\n"
            message += f"<b>Win Rate:</b> {stats.get('win_rate', 'N/A')}%\n"
            message += f"<b>Profit Factor:</b> {stats.get('profit_factor', 'N/A')}\n"
        
        self.send_message(message)
    
    def error_notification(self, error_msg, error_type="GENERAL", traceback_str=None):
        """
        Hata meydana geldiğinde çalıştır
        
        Args:
            error_msg: Hata mesajı
            error_type: ERROR tipi
            traceback_str: Traceback detayları
        """
        message = f"""
🚨 <b>ENGINE ERROR</b> 🚨

<b>Type:</b> {error_type}
<b>Time:</b> {datetime.now().strftime('%H:%M:%S')}

<b>Message:</b>
<code>{error_msg}</code>
"""
        
        if traceback_str:
            # Traceback'ı kes (Telegram char limit)
            tb_short = traceback_str[:500]
            message += f"\n<b>Traceback:</b>\n<code>{tb_short}</code>"
        
        self.send_message(message)
    
    def hourly_dashboard(self, equity, dd_percent, open_positions, perf_metrics, watchdog_status):
        """
        Saatlik dashboard (detaylı)
        
        Args:
            equity: Mevcut equity
            dd_percent: Drawdown yüzdesi
            open_positions: Açık pozisyon sayısı
            perf_metrics: Performans metrikleri dict
            watchdog_status: Watchdog status dict
        """
        message = f"""
📊 <b>HOURLY DASHBOARD</b> 📊

<b>⏰ Time:</b> {datetime.now().strftime('%H:%M:%S')}

<b>💰 EQUITY STATUS:</b>
<b>Current Equity:</b> ${equity:.2f}
<b>Drawdown:</b> <code>{dd_percent:.1f}%</code>
<b>Status:</b> {'🟢 HEALTHY' if dd_percent < 10 else '🟡 CAUTION' if dd_percent < 20 else '🔴 WARNING'}

<b>📈 PERFORMANCE:</b>
<b>Win Rate:</b> {perf_metrics.get('win_rate', 0):.1f}%
<b>Profit Factor:</b> {perf_metrics.get('profit_factor', 0):.2f}
<b>Total Trades:</b> {perf_metrics.get('total_trades', 0)}

<b>🏪 POSITIONS:</b>
<b>Open Positions:</b> {open_positions}/2

<b>🔔 WATCHDOG:</b>
<b>Health:</b> {watchdog_status.get('health', 'UNKNOWN')}
<b>Total Checks:</b> {watchdog_status.get('total_checks', 0)}
<b>Issues Found:</b> {watchdog_status.get('metrics', {}).get('issues_detected', 0)}
"""
        
        self.send_message(message)
    
    def trade_opened_notification(self, symbol, direction, entry_price, sl, risk, score, regime, mtf_bias):
        """
        Trade açıldığında çalıştır
        
        Args:
            symbol: Trading pair
            direction: LONG / SHORT
            entry_price: Entry fiyatı
            sl: Stop loss
            risk: Risk yüzdesi
            score: Trade score
            regime: Market regime
            mtf_bias: Multi-timeframe bias
        """
        direction_emoji = "📈" if direction == "LONG" else "📉"
        
        message = f"""
{direction_emoji} <b>TRADE OPENED</b> {direction_emoji}

<b>Symbol:</b> <code>{symbol}</code>
<b>Direction:</b> <b>{direction}</b>
<b>Entry:</b> ${entry_price:.2f}
<b>SL:</b> ${sl:.2f}

<b>📊 ANALYSIS:</b>
<b>Score:</b> {score:.2f}
<b>Risk:</b> {risk*100:.2f}%
<b>Regime:</b> {regime}
<b>MTF Bias:</b> {mtf_bias:.2f}

<b>⏰ Time:</b> {datetime.now().strftime('%H:%M:%S')}
"""
        
        self.send_message(message)
    
    def trade_closed_notification(self, symbol, direction, entry_price, exit_price, pnl, pnl_percent, duration):
        """
        Trade kapatıldığında çalıştır
        
        Args:
            symbol: Trading pair
            direction: LONG / SHORT
            entry_price: Entry fiyatı
            exit_price: Exit fiyatı
            pnl: PnL tutarı
            pnl_percent: PnL yüzdesi
            duration: Trade süresi (dakika)
        """
        pnl_emoji = "✅" if pnl > 0 else "❌"
        direction_emoji = "📈" if direction == "LONG" else "📉"
        
        message = f"""
{direction_emoji}{pnl_emoji} <b>TRADE CLOSED</b> {pnl_emoji}{direction_emoji}

<b>Symbol:</b> <code>{symbol}</code>
<b>Direction:</b> <b>{direction}</b>

<b>📊 TRADE DETAILS:</b>
<b>Entry:</b> ${entry_price:.2f}
<b>Exit:</b> ${exit_price:.2f}
<b>Duration:</b> {duration:.0f} min

<b>💵 P&L:</b>
<b>Realized PnL:</b> ${pnl:.2f}
<b>Return:</b> <code>{pnl_percent:.2f}%</code>

<b>⏰ Time:</b> {datetime.now().strftime('%H:%M:%S')}
"""
        
        self.send_message(message)
    
    def watchdog_alert(self, issue_type, details, severity="WARNING"):
        """
        Watchdog alert gönder
        
        Args:
            issue_type: Sorun tipi
            details: Sorun detayları
            severity: CRITICAL / WARNING / INFO
        """
        severity_emoji = "🔴" if severity == "CRITICAL" else "🟡" if severity == "WARNING" else "ℹ️"
        
        message = f"""
{severity_emoji} <b>WATCHDOG ALERT</b> {severity_emoji}

<b>Severity:</b> {severity}
<b>Issue:</b> {issue_type}

<b>Details:</b>
<code>{json.dumps(details, indent=2)[:300]}</code>

<b>⏰ Time:</b> {datetime.now().strftime('%H:%M:%S')}
"""
        
        self.send_message(message)
    
    def position_rebuild_notification(self, symbol, rebuilt=True, details=None):
        """
        Position rebuild gerçekleştiğinde
        
        Args:
            symbol: Trading pair
            rebuilt: Başarılı mı?
            details: Rebuild detayları
        """
        status_emoji = "✅" if rebuilt else "❌"
        
        message = f"""
🔄 <b>POSITION REBUILD</b> 🔄

<b>Symbol:</b> <code>{symbol}</code>
<b>Status:</b> {status_emoji} {'SUCCESS' if rebuilt else 'FAILED'}

"""
        
        if details and rebuilt:
            message += f"<b>Entry Price:</b> ${details.get('entry_price', 'N/A'):.2f}\n"
            message += f"<b>SL:</b> ${details.get('sl', 'N/A'):.2f}\n"
            message += f"<b>Current Price:</b> ${details.get('current_price', 'N/A'):.2f}\n"
            message += f"<b>Unrealized PnL:</b> ${details.get('unrealized_pnl', 'N/A'):.2f}\n"
        
        message += f"\n<b>⏰ Time:</b> {datetime.now().strftime('%H:%M:%S')}"
        
        self.send_message(message)
    
    def orphan_position_detected(self, symbol, exchange_symbol, state_symbol):
        """
        Orphan pozisyon tespit edildiğinde
        
        Args:
            symbol: Bulunan pozisyon
            exchange_symbol: Exchange'deki sembol
            state_symbol: State'teki sembol
        """
        message = f"""
⚠️ <b>ORPHAN POSITION DETECTED</b> ⚠️

<b>Exchange Position:</b> <code>{exchange_symbol}</code>
<b>State Position:</b> <code>{state_symbol}</code>

This position exists on exchange but not tracked in state!
Watchdog will attempt recovery.

<b>⏰ Time:</b> {datetime.now().strftime('%H:%M:%S')}
"""
        
        self.send_message(message)
    
    def reconciliation_status(self, symbol, issues_found, issues_list):
        """
        Reconciliation sonucu
        
        Args:
            symbol: Trading pair
            issues_found: Kaç sorun bulundu
            issues_list: Sorun listesi
        """
        status_emoji = "✅" if issues_found == 0 else "⚠️"
        
        message = f"""
🔄 <b>RECONCILIATION REPORT</b> 🔄

<b>Symbol:</b> <code>{symbol}</code>
<b>Issues Found:</b> {status_emoji} {issues_found}

"""
        
        if issues_found > 0:
            message += "<b>Issues:</b>\n"
            for issue in issues_list[:5]:  # İlk 5 sorun
                message += f"• {issue}\n"
        
        message += f"\n<b>⏰ Time:</b> {datetime.now().strftime('%H:%M:%S')}"
        
        self.send_message(message)
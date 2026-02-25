# ================= MULTI-PROCESS WATCHDOG ARCHITECTURE =================
# 24/7 monitoring: Main engine + Watchdog process
# Watchdog: State, Exchange, Stops, Lifecycle kontrol

import json
import time
import multiprocessing
import threading
from datetime import datetime
import traceback

class WatchdogEngine:
    """
    Bağımsız watchdog process
    
    Görevleri:
    1️⃣  State file integrity check
    2️⃣  Exchange ↔ State reconciliation
    3️⃣  Stop order sync verification
    4️⃣  Trade lifecycle consistency
    5️⃣  Recovery checkpoint monitoring
    6️⃣  Orphan position detection
    7️⃣  Emergency shutdown detection
    
    Main thread'den bağımsız çalışır.
    """
    
    def __init__(self, binance, state_manager, stop_manager=None, 
                 exchange_recon=None, trade_lifecycle=None,
                 check_interval=30, alert_webhook=None):
        """
        Args:
            binance: Binance client
            state_manager: State manager instance
            stop_manager: Stop manager instance
            exchange_recon: Exchange reconciliation engine
            trade_lifecycle: Trade lifecycle engine
            check_interval: Check interval in seconds (default 30)
            alert_webhook: Telegram/Discord webhook (opsiyonel)
        """
        self.binance = binance
        self.state_manager = state_manager
        self.stop_manager = stop_manager
        self.exchange_recon = exchange_recon
        self.trade_lifecycle = trade_lifecycle
        self.check_interval = check_interval
        self.alert_webhook = alert_webhook
        
        # ===== WATCHDOG STATE =====
        self.watchdog_log = "watchdog_log.json"
        self.emergency_file = "emergency_shutdown.flag"
        self.health_status = "HEALTHY"
        self.last_check = 0
        self.check_count = 0
        self.issues_found = 0
        
        # ===== METRIKS =====
        self.metrics = {
            "state_checks": 0,
            "reconciliation_checks": 0,
            "stop_checks": 0,
            "lifecycle_checks": 0,
            "issues_detected": 0,
            "critical_issues": 0,
            "recoveries_attempted": 0,
            "recoveries_successful": 0
        }
    
    def start_watchdog(self):
        """
        Watchdog process'ini başlat (separate thread'de)
        
        Kullanış:
            watchdog = WatchdogEngine(...)
            watchdog_thread = watchdog.start_watchdog()
        """
        print("🔔 Starting Watchdog Engine...")
        
        watchdog_thread = threading.Thread(
            target=self._watchdog_loop,
            daemon=True,
            name="WatchdogThread"
        )
        watchdog_thread.start()
        
        print("✅ Watchdog thread started (daemon)")
        return watchdog_thread
    
    def _watchdog_loop(self):
        """Ana watchdog loop"""
        print("🔴 Watchdog monitoring started...")
        
        while True:
            try:
                loop_start = time.time()
                
                # 1️⃣ STATE INTEGRITY CHECK
                self._check_state_integrity()
                
                # 2️⃣ EXCHANGE RECONCILIATION
                self._check_exchange_reconciliation()
                
                # 3️⃣ STOP ORDER SYNC
                self._check_stop_synchronization()
                
                # 4️⃣ TRADE LIFECYCLE
                self._check_trade_lifecycle()
                
                # 5️⃣ ORPHAN POSITION DETECTION
                self._detect_orphan_positions()
                
                # 6️⃣ RECOVERY CHECKPOINT
                self._check_recovery_checkpoint()
                
                # 7️⃣ EMERGENCY SHUTDOWN CHECK
                self._check_emergency_shutdown()
                
                # 8️⃣ HEALTH STATUS UPDATE
                self._update_health_status()
                
                loop_duration = time.time() - loop_start
                
                self.check_count += 1
                self.last_check = time.time()
                
                # Özetini log'la (her 10 check'te)
                if self.check_count % 10 == 0:
                    self._log_summary()
                
                # Sleep (interval'e bölüştür)
                sleep_time = max(self.check_interval - loop_duration, 1)
                time.sleep(sleep_time)
            
            except KeyboardInterrupt:
                print("🛑 Watchdog interrupted")
                break
            
            except Exception as e:
                print(f"❌ Watchdog error: {e}")
                traceback.print_exc()
                self.metrics["critical_issues"] += 1
                time.sleep(self.check_interval)
    
    def _check_state_integrity(self):
        """State file'ının integrity'sini kontrol et"""
        try:
            self.metrics["state_checks"] += 1
            
            state = self.state_manager.load_state()
            
            if not isinstance(state, dict):
                raise ValueError("State is not a dict")
            
            # Zorunlu alanlar var mı?
            required_fields = ["peak", "entry", "direction", "sl"]
            missing = [f for f in required_fields if f not in state]
            
            if missing:
                print(f"⚠️  WATCHDOG: Missing state fields: {missing}")
                self.metrics["issues_detected"] += 1
                self._log_issue("state_missing_fields", {"missing_fields": missing})
                return False
            
            # Peak valid mi?
            if state.get("peak", 0) <= 0:
                print(f"⚠️  WATCHDOG: Invalid peak value: {state.get('peak')}")
                self.metrics["issues_detected"] += 1
                self._log_issue("state_invalid_peak", {"peak": state.get("peak")})
                return False
            
            print(f"✅ State integrity OK")
            return True
        
        except Exception as e:
            print(f"❌ State integrity check failed: {e}")
            self.metrics["critical_issues"] += 1
            self._log_issue("state_integrity_error", {"error": str(e)})
            return False
    
    def _check_exchange_reconciliation(self):
        """Exchange ↔ State reconciliation'ı kontrol et"""
        try:
            self.metrics["reconciliation_checks"] += 1
            
            if not self.exchange_recon:
                print("⚠️  Exchange reconciliation engine not available")
                return False
            
            # Exchange'den positions al
            try:
                positions = self.binance.fetch_positions()
                open_positions = [p for p in positions if float(p.get('contracts', 0)) != 0]
            except Exception as e:
                print(f"⚠️  Could not fetch positions: {e}")
                return False
            
            if not open_positions:
                print(f"✅ No positions to reconcile")
                return True
            
            # State al
            state = self.state_manager.load_state()
            
            # Her position'ı reconcile et
            issues_in_recon = 0
            for position in open_positions:
                symbol = position['symbol']
                state_updated, issues = self.exchange_recon.reconcile_position(
                    symbol, state, open_positions
                )
                
                if issues:
                    issues_in_recon += len(issues)
                    self.metrics["issues_detected"] += len(issues)
                    self._log_issue("reconciliation_issue", {
                        "symbol": symbol,
                        "issues": issues
                    })
            
            if issues_in_recon > 0:
                print(f"⚠️  Reconciliation found {issues_in_recon} issues")
                return False
            
            print(f"✅ Reconciliation OK")
            return True
        
        except Exception as e:
            print(f"❌ Reconciliation check failed: {e}")
            self.metrics["critical_issues"] += 1
            return False
    
    def _check_stop_synchronization(self):
        """Stop order'lar senkron mu kontrol et"""
        try:
            self.metrics["stop_checks"] += 1
            
            if not self.stop_manager:
                print("⚠️  Stop manager not available")
                return False
            
            # Exchange'den positions al
            try:
                positions = self.binance.fetch_positions()
                open_positions = [p for p in positions if float(p.get('contracts', 0)) != 0]
            except Exception as e:
                print(f"⚠️  Could not fetch positions: {e}")
                return False
            
            if not open_positions:
                print(f"✅ No positions, stop check OK")
                return True
            
            # State al
            state = self.state_manager.load_state()
            
            # Her position için stop'ları kontrol et
            sync_issues = 0
            for position in open_positions:
                symbol = position['symbol']
                
                # Exchange'deki stops
                try:
                    active_stops = self.stop_manager.get_active_stops(symbol)
                except:
                    active_stops = []
                
                # State'teki SL
                state_sl = state.get('sl')
                
                if active_stops and state_sl:
                    stop_price = active_stops[0].get('stopPrice', 0)
                    diff = abs(stop_price - state_sl) / state_sl if state_sl != 0 else 0
                    
                    if diff > 0.005:  # %0.5 tolerance
                        print(f"⚠️  Stop sync issue on {symbol}")
                        print(f"    Exchange: {stop_price}")
                        print(f"    State: {state_sl}")
                        sync_issues += 1
                        self.metrics["issues_detected"] += 1
                        
                        # Auto-fix: Force resync
                        try:
                            self.exchange_recon.force_resync_stops(
                                symbol,
                                state,
                                state.get('direction'),
                                abs(float(position.get('contracts', 0)))
                            )
                            self.metrics["recoveries_attempted"] += 1
                            self.metrics["recoveries_successful"] += 1
                        except Exception as e:
                            print(f"❌ Force resync failed: {e}")
                
                elif not active_stops and state_sl:
                    print(f"⚠️  Stop order missing on {symbol}")
                    sync_issues += 1
                    self.metrics["issues_detected"] += 1
            
            if sync_issues > 0:
                print(f"⚠️  Found {sync_issues} stop sync issues")
                return False
            
            print(f"✅ Stop synchronization OK")
            return True
        
        except Exception as e:
            print(f"❌ Stop sync check failed: {e}")
            self.metrics["critical_issues"] += 1
            return False
    
    def _check_trade_lifecycle(self):
        """Trade lifecycle consistency'si kontrol et"""
        try:
            self.metrics["lifecycle_checks"] += 1
            
            if not self.trade_lifecycle:
                print("⚠️  Trade lifecycle engine not available")
                return True  # Skip
            
            # Exchange'den positions al
            try:
                positions = self.binance.fetch_positions()
                open_positions = [p for p in positions if float(p.get('contracts', 0)) != 0]
            except Exception as e:
                print(f"⚠️  Could not fetch positions: {e}")
                return False
            
            state = self.state_manager.load_state()
            
            # Aktif trade'leri kontrol et
            active_trades = self.trade_lifecycle.active_trades
            lifecycle_issues = 0
            
            for symbol, trade in active_trades.items():
                is_consistent = self.trade_lifecycle.verify_state_consistency(
                    symbol, state, open_positions
                )
                
                if not is_consistent:
                    lifecycle_issues += 1
                    self.metrics["issues_detected"] += 1
            
            if lifecycle_issues > 0:
                print(f"⚠️  Found {lifecycle_issues} lifecycle issues")
                return False
            
            print(f"✅ Trade lifecycle OK")
            return True
        
        except Exception as e:
            print(f"⚠️  Lifecycle check failed: {e}")
            return False
    
    def _detect_orphan_positions(self):
        """Öksüz pozisyonları tespit et (exchange'de var ama state'de yok)"""
        try:
            try:
                positions = self.binance.fetch_positions()
                open_positions = [p for p in positions if float(p.get('contracts', 0)) != 0]
            except Exception as e:
                print(f"⚠️  Could not fetch positions: {e}")
                return False
            
            if not open_positions:
                print(f"✅ No orphan positions")
                return True
            
            state = self.state_manager.load_state()
            state_symbol = None
            
            # State'te açık pozisyon var mı?
            if state.get('entry') and state.get('direction'):
                state_symbol = state.get('symbol')  # State'te symbol olmalı
            
            # Exchange'deki positions
            for position in open_positions:
                symbol = position['symbol']
                
                if symbol != state_symbol:
                    print(f"❌ ORPHAN POSITION DETECTED: {symbol}")
                    print(f"    Exchange: {symbol}")
                    print(f"    State: {state_symbol}")
                    
                    self.metrics["issues_detected"] += 1
                    self.metrics["critical_issues"] += 1
                    
                    self._log_issue("orphan_position", {
                        "exchange_symbol": symbol,
                        "state_symbol": state_symbol
                    })
                    
                    # Alert gönder
                    self._send_alert(f"🚨 ORPHAN POSITION: {symbol}")
                    
                    return False
            
            print(f"✅ No orphan positions")
            return True
        
        except Exception as e:
            print(f"⚠️  Orphan position check failed: {e}")
            return False
    
    def _check_recovery_checkpoint(self):
        """Recovery checkpoint'i kontrol et"""
        try:
            import os
            
            recovery_file = "recovery_checkpoint.json"
            
            if os.path.exists(recovery_file):
                # Checkpoint var - eski mi?
                file_age = time.time() - os.path.getmtime(recovery_file)
                
                if file_age > 3600:  # 1 saatten eski
                    print(f"⚠️  WATCHDOG: Old recovery checkpoint ({file_age/60:.0f} min old)")
                    print(f"    Removing stale checkpoint...")
                    
                    try:
                        os.remove(recovery_file)
                        print(f"✅ Stale checkpoint removed")
                    except Exception as e:
                        print(f"❌ Could not remove checkpoint: {e}")
                        self.metrics["issues_detected"] += 1
                else:
                    print(f"⚠️  WATCHDOG: Recovery checkpoint present ({file_age/60:.1f} min old)")
                    print(f"    Engine may be in recovery mode")
            
            print(f"✅ Recovery checkpoint check OK")
            return True
        
        except Exception as e:
            print(f"⚠️  Recovery checkpoint check failed: {e}")
            return False
    
    def _check_emergency_shutdown(self):
        """Emergency shutdown flag'ini kontrol et"""
        try:
            import os
            
            if os.path.exists(self.emergency_file):
                print(f"🚨 EMERGENCY SHUTDOWN FLAG DETECTED!")
                print(f"    Main engine should shut down immediately")
                
                # Flag'ı oku
                try:
                    with open(self.emergency_file, "r") as f:
                        reason = f.read().strip()
                    print(f"    Reason: {reason}")
                except:
                    pass
                
                self._send_alert("🚨 EMERGENCY SHUTDOWN REQUESTED")
                
                return False
            
            return True
        
        except Exception as e:
            print(f"⚠️  Emergency check failed: {e}")
            return False
    
    def _update_health_status(self):
        """Watchdog health status'unu güncelle"""
        try:
            critical_issues = self.metrics.get("critical_issues", 0)
            total_issues = self.metrics.get("issues_detected", 0)
            
            if critical_issues > 5:
                self.health_status = "CRITICAL"
            elif total_issues > 10:
                self.health_status = "DEGRADED"
            else:
                self.health_status = "HEALTHY"
            
            print(f"🔔 Watchdog health: {self.health_status}")
        
        except Exception as e:
            print(f"⚠️  Health status update failed: {e}")
    
    def _send_alert(self, message):
        """Alert gönder"""
        if self.alert_webhook:
            try:
                import requests
                requests.post(self.alert_webhook, json={"text": message}, timeout=5)
            except:
                pass
    
    def _log_issue(self, issue_type, details):
        """Sorunu log'la"""
        try:
            logs = []
            try:
                with open(self.watchdog_log, "r") as f:
                    logs = json.load(f)
            except:
                logs = []
            
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "issue_type": issue_type,
                "details": details,
                "health_status": self.health_status
            }
            
            logs.append(log_entry)
            
            # Son 1000 log tutun
            if len(logs) > 1000:
                logs = logs[-1000:]
            
            with open(self.watchdog_log, "w") as f:
                json.dump(logs, f, indent=2)
        except:
            pass
    
    def _log_summary(self):
        """Özet bilgi log'la"""
        print("\n" + "="*80)
        print("🔔 WATCHDOG SUMMARY (last 10 checks)")
        print("="*80)
        print(f"Total checks: {self.check_count}")
        print(f"Issues detected: {self.metrics['issues_detected']}")
        print(f"Critical issues: {self.metrics['critical_issues']}")
        print(f"Recoveries attempted: {self.metrics['recoveries_attempted']}")
        print(f"Recoveries successful: {self.metrics['recoveries_successful']}")
        print(f"Health status: {self.health_status}")
        print("="*80 + "\n")
    
    def get_watchdog_status(self):
        """Watchdog status'unu al"""
        return {
            "health": self.health_status,
            "last_check": self.last_check,
            "total_checks": self.check_count,
            "metrics": self.metrics
        }
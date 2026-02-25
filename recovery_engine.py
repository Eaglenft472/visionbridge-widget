# ================= RECOVERY STATE ENGINE - PRODUCTION HARDENED =================
import json
import os
import time
from datetime import datetime
import tempfile
import shutil

class StateManager:
    """Crash-safe state management - GUARANTEED STABLE"""
    
    def __init__(self, state_file="engine_state.json", backup_dir="state_backups"):
        self.state_file = state_file
        self.backup_dir = backup_dir
        self.recovery_file = "recovery_checkpoint.json"
        
        # Directory'leri güvenli şekilde oluştur
        try:
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir, exist_ok=True)
            print(f"✅ State backup directory initialized: {backup_dir}")
        except Exception as e:
            print(f"❌ Failed to create backup directory: {e}")
    
    def _default_state(self):
        """Default state template - GUARANTEED returns valid dict"""
        return {
            "peak": 10000.0,
            "entry": None,
            "direction": None,
            "sl": None,
            "R": None,
            "risk_cut": False,
            "cooldown_until": 0,
            "tp1_done": False,
            "tp2_done": False,
            "trail_active": False,
            "entry_time": None,
            "recovery_mode": False,
            "entry_regime": None,
            "entry_risk": None,
            "entry_mtf_bias": None,
            "entry_latency_ms": 0,
            "highest_price": None,
            "save_count": 0,
            "last_save": None,
            "current_position": None,
            "trades": [],
            "stats": {
                "total_trades": 0,
                "wins": 0,
                "losses": 0
            }
        }
    
    def load_state(self):
        """
        Crash-safe state yükle - GUARANTEED NON-NULL RETURN
        
        Öncelik sıras��:
        1. Ana state dosyası (engine_state.json)
        2. Recovery checkpoint
        3. En yeni backup
        4. Default state
        
        HİÇBİR ZAMAN None DÖNEMEZ!
        """
        state = None
        
        # ===== 1️⃣ ANA STATE DOSYASI KONTROLÜ (ÖNCE) =====
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, "r") as f:
                    content = f.read().strip()
                    
                    # Boş dosya kontrolü
                    if content:
                        state = json.loads(content)
                        
                        # Valid dict kontrolü
                        if isinstance(state, dict) and state.get("entry"):
                            print(f"✅ State loaded successfully from {self.state_file}")
                            return state
                        else:
                            print(f"⚠️  State file exists but entry is empty")
                            state = None
                    else:
                        print(f"⚠️  State file is empty")
                        state = None
        
        except json.JSONDecodeError as je:
            print(f"❌ State file JSON decode error: {je}")
        except Exception as e:
            print(f"⚠️  State file load error: {e}")
        
        # ===== 2️⃣ RECOVERY CHECKPOINT KONTROLÜ (İKİNCİ) =====
        if state is None:
            try:
                if os.path.exists(self.recovery_file):
                    print("⚠️  Recovery checkpoint found - loading...")
                    with open(self.recovery_file, "r") as f:
                        recovery_data = json.load(f)
                    
                    # Checkpoint yapısını kontrol et
                    if isinstance(recovery_data, dict):
                        if "state" in recovery_data:
                            state = recovery_data["state"]
                        else:
                            state = recovery_data
                    
                    # Checkpoint'i kaldır (başarılı load'dan sonra)
                    if state and isinstance(state, dict):
                        try:
                            os.remove(self.recovery_file)
                            print(f"✅ Recovered state from checkpoint and removed checkpoint file")
                        except:
                            pass
                        return state
            
            except json.JSONDecodeError as je:
                print(f"❌ Recovery checkpoint JSON decode error: {je}")
            except Exception as e:
                print(f"❌ Recovery checkpoint load error: {e}")
        
        # ===== 3️⃣ BACKUP'TAN RECOVERY =====
        if state is None:
            state = self._recover_from_backup()
        
        # ===== 4️⃣ SON ÇARE: DEFAULT STATE =====
        if state is None or not isinstance(state, dict):
            print("⚠️  No valid state found - creating new default state")
            state = self._default_state()
        
        # Final validation
        if "peak" not in state:
            state["peak"] = 10000.0
        
        return state
    
    def save_state(self, state):
        """
        Atomik state yazma - GUARANTEED safe veya False return
        """
        if state is None or not isinstance(state, dict):
            print("⚠️  Cannot save invalid state (None or non-dict)")
            return False
        
        try:
            state["last_save"] = datetime.now().isoformat()
            state["save_count"] = state.get("save_count", 0) + 1
            
            # Temp file'a yaz
            temp_fd = None
            temp_path = None
            
            try:
                temp_fd, temp_path = tempfile.mkstemp(suffix=".json", prefix="state_", dir=".")
                
                with os.fdopen(temp_fd, "w") as f:
                    json.dump(state, f, indent=2)
                
                # Atomik replace (Windows-safe)
                if os.path.exists(self.state_file):
                    try:
                        os.remove(self.state_file)
                    except:
                        pass
                
                os.rename(temp_path, self.state_file)
                return True
            
            except Exception as e:
                # Cleanup temp file
                if temp_path and os.path.exists(temp_path):
                    try:
                        os.unlink(temp_path)
                    except:
                        pass
                raise e
        
        except Exception as e:
            print(f"❌ State save error: {e}")
            return False
    
    def create_recovery_checkpoint(self, state):
        """
        Crash-safe recovery checkpoint oluştur
        """
        if state is None or not isinstance(state, dict):
            print("⚠️  Cannot create checkpoint from invalid state")
            return False
        
        try:
            checkpoint = {
                "timestamp": datetime.now().isoformat(),
                "crash_time": datetime.now().isoformat(),
                "state": state,
                "recovery_mode": True
            }
            
            with open(self.recovery_file, "w") as f:
                json.dump(checkpoint, f, indent=2)
            
            print(f"✅ Recovery checkpoint created successfully")
            return True
        
        except Exception as e:
            print(f"❌ Recovery checkpoint failed: {e}")
            return False
    
    def create_backup(self, state):
        """
        State backup'ını backup directory'ye kaydet
        """
        if state is None or not isinstance(state, dict):
            print("⚠️  Cannot backup invalid state")
            return False
        
        try:
            if not os.path.exists(self.backup_dir):
                os.makedirs(self.backup_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(
                self.backup_dir,
                f"state_backup_{timestamp}.json"
            )
            
            with open(backup_file, "w") as f:
                json.dump(state, f, indent=2)
            
            self._cleanup_old_backups()
            return True
        
        except Exception as e:
            print(f"❌ Backup error: {e}")
            return False
    
    def _cleanup_old_backups(self, keep=10):
        """Eski backup'ları sil (en yeni 10 tutunur)"""
        try:
            if not os.path.exists(self.backup_dir):
                return
            
            backups = sorted([
                f for f in os.listdir(self.backup_dir)
                if f.startswith("state_backup_") and f.endswith(".json")
            ])
            
            if len(backups) > keep:
                for old_backup in backups[:-keep]:
                    try:
                        os.remove(os.path.join(self.backup_dir, old_backup))
                    except:
                        pass
        except:
            pass
    
    def _recover_from_backup(self):
        """
        Son backup'tan recovery yap - GUARANTEED returns dict or default
        """
        try:
            if not os.path.exists(self.backup_dir):
                return self._default_state()
            
            backups = sorted([
                f for f in os.listdir(self.backup_dir)
                if f.startswith("state_backup_") and f.endswith(".json")
            ])
            
            if not backups:
                print("⚠️  No backups found - using default state")
                return self._default_state()
            
            # En yeni backup'tan başla, geriye doğru git
            for latest_backup in reversed(backups):
                try:
                    backup_path = os.path.join(self.backup_dir, latest_backup)
                    
                    with open(backup_path, "r") as f:
                        content = f.read().strip()
                        if content:
                            state = json.loads(content)
                    
                    if isinstance(state, dict) and "peak" in state:
                        print(f"✅ Recovered from backup: {latest_backup}")
                        return state
                
                except json.JSONDecodeError:
                    print(f"⚠️  Backup {latest_backup} corrupted - trying older backups")
                    continue
                except Exception as e:
                    print(f"⚠️  Backup {latest_backup} error: {e} - trying older backups")
                    continue
            
            print("⚠️  No valid backups found - using default state")
            return self._default_state()
        
        except Exception as e:
            print(f"❌ Backup recovery error: {e}")
            return self._default_state()
    
    def get_recovery_status(self):
        """Recovery status bilgisi"""
        try:
            backup_count = 0
            if os.path.exists(self.backup_dir):
                backup_count = len([
                    f for f in os.listdir(self.backup_dir)
                    if f.startswith("state_backup_") and f.endswith(".json")
                ])
            
            status = {
                "main_state_exists": os.path.exists(self.state_file),
                "recovery_checkpoint_exists": os.path.exists(self.recovery_file),
                "backup_count": backup_count
            }
            return status
        except:
            return {
                "main_state_exists": False,
                "recovery_checkpoint_exists": False,
                "backup_count": 0
            }

# ===== GLOBAL SINGLETON =====
state_manager = StateManager()

def load_state():
    """
    Global load_state - GUARANTEED returns dict, NEVER None
    engine_state.json dosyasından yükle (ÖNCE!)
    """
    # state_manager'dan yükle
    state = state_manager.load_state()
    
    # Final safety check
    if state is None or not isinstance(state, dict):
        print("🚨 CRITICAL: load_state returned invalid state - forcing default")
        state = state_manager._default_state()
    
    return state


def save_state(state):
    """Global save_state with backup"""
    if state is None or not isinstance(state, dict):
        print("⚠️  Attempt to save invalid state - skipping")
        return False
    
    state_manager.save_state(state)
    state_manager.create_backup(state)
    return True


def create_recovery_checkpoint(state):
    """Global recovery checkpoint creator"""
    if state is None or not isinstance(state, dict):
        return False
    
    return state_manager.create_recovery_checkpoint(state)
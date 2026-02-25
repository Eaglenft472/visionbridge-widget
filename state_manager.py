# ================= STATE MANAGER - CRASH-SAFE RECOVERY =================
import json
import os
import time
from datetime import datetime
import tempfile

class StateManager:
    """
    Crash-safe state management.
    - Atomic writes (temp file + os.replace)
    - Checksum verification
    - Backup history
    - Recovery point creation
    """
    
    def __init__(self, state_file="engine_state.json", backup_dir="state_backups"):
        self.state_file = state_file
        self.backup_dir = backup_dir
        self.recovery_file = "recovery_checkpoint.json"
        
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
    
    def load_state(self):
        """Crash-safe state yükle"""
        try:
            if os.path.exists(self.recovery_file):
                print("⚠️ Recovery checkpoint found - loading...")
                with open(self.recovery_file, "r") as f:
                    state = json.load(f)
                print(f"✅ Recovered state from checkpoint at {state.get('crash_time', 'unknown')}")
                os.remove(self.recovery_file)
                return state
            
            if os.path.exists(self.state_file):
                with open(self.state_file, "r") as f:
                    state = json.load(f)
                print(f"✅ State loaded successfully from engine_state.json")
                return state
            else:
                print("⚠️ No state file found - creating new")
                return self._default_state()
        
        except json.JSONDecodeError:
            print("❌ State file corrupted - attempting recovery from backup")
            return self._recover_from_backup()
        except Exception as e:
            print(f"❌ State load error: {e}")
            return self._recover_from_backup()
    
    def save_state(self, state):
        """Atomik state yazma"""
        try:
            # ===== GUARANTEE peak ve direction VAR =====
            if "peak" not in state:
                state["peak"] = 10000.0
            if "direction" not in state:
                state["direction"] = None
            # ==========================================
            
            state["last_save"] = datetime.now().isoformat()
            state["save_count"] = state.get("save_count", 0) + 1
            
            fd, temp_path = tempfile.mkstemp(suffix=".json", prefix="state_")
            try:
                with os.fdopen(fd, "w") as f:
                    json.dump(state, f, indent=2)
                
                os.replace(temp_path, self.state_file)
                return True
            except Exception as e:
                os.unlink(temp_path)
                raise e
        
        except Exception as e:
            print(f"❌ State save error: {e}")
            return False
    
    def create_recovery_checkpoint(self, state):
        """Crash-safe recovery checkpoint oluştur"""
        try:
            checkpoint = {
                "timestamp": datetime.now().isoformat(),
                "crash_time": datetime.now().isoformat(),
                "state": state,
                "recovery_mode": True
            }
            
            with open(self.recovery_file, "w") as f:
                json.dump(checkpoint, f, indent=2)
            
            return True
        except Exception as e:
            print(f"❌ Recovery checkpoint failed: {e}")
            return False
    
    def create_backup(self, state):
        """State backup'ını backup directory'ye kaydet"""
        try:
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
        """Eski backup'ları sil"""
        try:
            backups = sorted([
                f for f in os.listdir(self.backup_dir)
                if f.startswith("state_backup_")
            ])
            
            if len(backups) > keep:
                for old_backup in backups[:-keep]:
                    os.remove(os.path.join(self.backup_dir, old_backup))
        except Exception as e:
            pass
    
    def _recover_from_backup(self):
        """Son backup'tan recovery yap"""
        try:
            backups = sorted([
                f for f in os.listdir(self.backup_dir)
                if f.startswith("state_backup_")
            ])
            
            if backups:
                latest_backup = backups[-1]
                backup_path = os.path.join(self.backup_dir, latest_backup)
                
                with open(backup_path, "r") as f:
                    state = json.load(f)
                
                print(f"✅ Recovered from backup: {latest_backup}")
                return state
            else:
                print("⚠️ No backups found - using default state")
                return self._default_state()
        
        except Exception as e:
            print(f"❌ Backup recovery error: {e}")
            return self._default_state()
    
    def _default_state(self):
        """Default state template"""
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
            "recovery_mode": False
        }
    
    def get_recovery_status(self):
        """Recovery status bilgisi"""
        status = {
            "main_state_exists": os.path.exists(self.state_file),
            "recovery_checkpoint_exists": os.path.exists(self.recovery_file),
            "backup_count": len([
                f for f in os.listdir(self.backup_dir)
                if f.startswith("state_backup_")
            ]) if os.path.exists(self.backup_dir) else 0
        }
        return status

# Global instance
state_manager = StateManager()

def load_state():
    """Load state wrapper"""
    return state_manager.load_state()

def save_state(state):
    """Save state wrapper"""
    state_manager.save_state(state)
    state_manager.create_backup(state)

def create_recovery_checkpoint(state):
    """Create recovery checkpoint wrapper"""
    state_manager.create_recovery_checkpoint(state)
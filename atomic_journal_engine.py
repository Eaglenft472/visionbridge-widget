# ================= ATOMIC JOURNAL WRITE ENGINE =================
import os
import json
import tempfile

class AtomicJournal:
    def __init__(self, journal_path="trade_journal.json"):
        self.journal_path = journal_path
    
    def write_atomic(self, data):
        """Atomik yazma"""
        try:
            journal = []
            if os.path.exists(self.journal_path):
                with open(self.journal_path, "r") as f:
                    journal = json.load(f)
            
            journal.append(data)
            
            fd, temp_path = tempfile.mkstemp(suffix=".json", prefix="journal_")
            try:
                with os.fdopen(fd, "w") as f:
                    json.dump(journal[-1000:], f, indent=2)
                
                os.replace(temp_path, self.journal_path)
                return True
            except Exception as e:
                os.unlink(temp_path)
                raise e
        
        except Exception as e:
            print(f"❌ Atomic journal write failed: {e}")
            return False
    
    def read_safe(self):
        """Güvenli okuma"""
        try:
            if not os.path.exists(self.journal_path):
                return []
            with open(self.journal_path, "r") as f:
                return json.load(f)
        except:
            return []
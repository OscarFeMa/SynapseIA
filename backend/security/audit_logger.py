"""
Synapse Security: Immutable Audit Log
Records all security-relevant events in an append-only format.
"""
import json
import hashlib
import datetime
import os
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class AuditEntry:
    """Immutable audit log entry."""
    timestamp: str
    event_id: str
    event_type: str
    subject: str
    action: str
    details: Dict[str, Any]
    source_ip: Optional[str]
    user_agent: Optional[str]
    success: bool
    previous_hash: str
    current_hash: str = ""
    
    def compute_hash(self) -> str:
        """Compute SHA-256 hash of entry contents."""
        data = {
            "timestamp": self.timestamp,
            "event_id": self.event_id,
            "event_type": self.event_type,
            "subject": self.subject,
            "action": self.action,
            "details": self.details,
            "source_ip": self.source_ip,
            "user_agent": self.user_agent,
            "success": self.success,
            "previous_hash": self.previous_hash
        }
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    def finalize(self):
        """Compute and set the current hash."""
        self.current_hash = self.compute_hash()

class AuditLogger:
    """Append-only audit logger with chain verification."""
    
    def __init__(self, log_dir: str = "audit_logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.current_file = self._get_today_file()
        self.last_hash = self._get_last_hash()
        self.buffer: List[AuditEntry] = []
        self.buffer_size = 10  # Flush after N entries
        
    def _get_today_file(self) -> Path:
        """Get today's audit log file path."""
        date_str = datetime.datetime.utcnow().strftime("%Y-%m-%d")
        return self.log_dir / f"audit_{date_str}.log"
    
    def _get_last_hash(self) -> str:
        """Get the hash of the last entry (for chain continuity)."""
        today_file = self._get_today_file()
        
        if not today_file.exists():
            # Check yesterday's file for continuity
            yesterday = datetime.datetime.utcnow() - datetime.timedelta(days=1)
            yesterday_file = self.log_dir / f"audit_{yesterday.strftime('%Y-%m-%d')}.log"
            
            if yesterday_file.exists():
                try:
                    with open(yesterday_file, 'r') as f:
                        lines = f.readlines()
                        if lines:
                            last_entry = json.loads(lines[-1])
                            return last_entry.get("current_hash", "")
                except Exception as e:
                    logger.error(f"Failed to read yesterday's hash: {e}")
            
            return "GENESIS"  # Genesis block hash
        
        try:
            with open(today_file, 'r') as f:
                lines = f.readlines()
                if lines:
                    last_entry = json.loads(lines[-1])
                    return last_entry.get("current_hash", "")
        except Exception as e:
            logger.error(f"Failed to read last hash: {e}")
        
        return "GENESIS"
    
    def log(self, 
            event_type: str, 
            subject: str, 
            action: str, 
            details: Dict[str, Any],
            success: bool,
            source_ip: Optional[str] = None,
            user_agent: Optional[str] = None) -> str:
        """
        Log an audit entry.
        Returns the event_id.
        """
        import uuid
        
        timestamp = datetime.datetime.utcnow().isoformat() + "Z"
        event_id = str(uuid.uuid4())
        
        entry = AuditEntry(
            timestamp=timestamp,
            event_id=event_id,
            event_type=event_type,
            subject=subject,
            action=action,
            details=details,
            source_ip=source_ip,
            user_agent=user_agent,
            success=success,
            previous_hash=self.last_hash
        )
        
        entry.finalize()
        
        # Update last hash for next entry
        self.last_hash = entry.current_hash
        
        # Add to buffer
        self.buffer.append(entry)
        
        # Flush if buffer is full
        if len(self.buffer) >= self.buffer_size:
            self._flush_buffer()
        
        return event_id
    
    def _flush_buffer(self):
        """Write buffered entries to disk."""
        if not self.buffer:
            return
        
        # Check if we need to rotate to a new file
        current_file = self._get_today_file()
        if current_file != self.current_file:
            self.current_file = current_file
        
        try:
            with open(self.current_file, 'a') as f:
                for entry in self.buffer:
                    json_line = json.dumps(asdict(entry), sort_keys=True)
                    f.write(json_line + "\n")
            
            self.buffer.clear()
            
        except Exception as e:
            logger.critical(f"AUDIT LOG WRITE FAILURE: {e}")
            # Fallback: print to stderr (should never happen in prod)
            for entry in self.buffer:
                print(f"AUDIT_FALLBACK: {json.dumps(asdict(entry))}", flush=True)
            self.buffer.clear()
    
    def flush(self):
        """Force flush the buffer."""
        self._flush_buffer()
    
    def verify_chain(self, date: Optional[str] = None) -> bool:
        """
        Verify the integrity of the audit chain.
        Returns True if all hashes are valid.
        """
        if date is None:
            date = datetime.datetime.utcnow().strftime("%Y-%m-%d")
        
        log_file = self.log_dir / f"audit_{date}.log"
        
        if not log_file.exists():
            logger.warning(f"Audit file for {date} not found")
            return True  # No file = nothing to verify
        
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
            
            if not lines:
                return True
            
            prev_hash = "GENESIS" if date != datetime.datetime.utcnow().strftime("%Y-%m-%d") else self._get_last_hash_from_yesterday()
            
            for line in lines:
                entry_data = json.loads(line)
                
                # Recompute hash
                entry = AuditEntry(**entry_data)
                computed_hash = entry.compute_hash()
                
                # Verify previous hash links correctly
                if entry_data.get("previous_hash") != prev_hash:
                    logger.error(f"Chain broken at {entry_data['event_id']}: previous_hash mismatch")
                    return False
                
                # Verify current hash
                if entry_data.get("current_hash") != computed_hash:
                    logger.error(f"Hash mismatch at {entry_data['event_id']}")
                    return False
                
                prev_hash = entry_data["current_hash"]
            
            return True
            
        except Exception as e:
            logger.error(f"Chain verification failed: {e}")
            return False
    
    def _get_last_hash_from_yesterday(self) -> str:
        """Get last hash from yesterday's log."""
        yesterday = datetime.datetime.utcnow() - datetime.timedelta(days=1)
        yesterday_file = self.log_dir / f"audit_{yesterday.strftime('%Y-%m-%d')}.log"
        
        if yesterday_file.exists():
            try:
                with open(yesterday_file, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        last_entry = json.loads(lines[-1])
                        return last_entry.get("current_hash", "")
            except Exception:
                pass
        
        return "GENESIS"
    
    def search(self, 
               event_type: Optional[str] = None,
               subject: Optional[str] = None,
               start_date: Optional[str] = None,
               end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search audit logs with filters."""
        results = []
        
        # Determine date range to search
        if start_date is None:
            start_date = (datetime.datetime.utcnow() - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
        if end_date is None:
            end_date = datetime.datetime.utcnow().strftime("%Y-%m-%d")
        
        current = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.datetime.strptime(end_date, "%Y-%m-%d")
        
        while current <= end:
            date_str = current.strftime("%Y-%m-%d")
            log_file = self.log_dir / f"audit_{date_str}.log"
            
            if log_file.exists():
                try:
                    with open(log_file, 'r') as f:
                        for line in f:
                            entry = json.loads(line)
                            
                            # Apply filters
                            if event_type and entry.get("event_type") != event_type:
                                continue
                            if subject and entry.get("subject") != subject:
                                continue
                            
                            results.append(entry)
                except Exception as e:
                    logger.error(f"Error reading {log_file}: {e}")
            
            current += datetime.timedelta(days=1)
        
        return results

# Global instance
audit_logger = AuditLogger()

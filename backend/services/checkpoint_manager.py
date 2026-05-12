"""
System State Snapshot and Checkpointing for Synapse Council.
Enables recovery from crashes by saving and restoring system state.
"""
import json
import os
import time
import threading
import pickle
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class StateSnapshot:
    """Represents a point-in-time snapshot of system state."""
    
    def __init__(self, data: Dict[str, Any], timestamp: float = None):
        self.data = data
        self.timestamp = timestamp or time.time()
        self.created_at = datetime.fromtimestamp(self.timestamp).isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "created_at": self.created_at,
            "data": self.data
        }
    
    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'StateSnapshot':
        return cls(data=d["data"], timestamp=d["timestamp"])

class CheckpointManager:
    """Manages system state checkpoints for crash recovery."""
    
    def __init__(
        self,
        checkpoint_dir: str = "./checkpoints",
        max_checkpoints: int = 5,
        auto_save_interval: float = 300.0  # 5 minutes
    ):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.max_checkpoints = max_checkpoints
        self.auto_save_interval = auto_save_interval
        
        self._state_providers: Dict[str, callable] = {}
        self._state_restorers: Dict[str, callable] = {}
        self._last_checkpoint_time: float = 0
        self._auto_save_thread: Optional[threading.Thread] = None
        self._stop_auto_save = threading.Event()
        self._lock = threading.Lock()
        
        # Create checkpoint directory
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"CheckpointManager initialized at {self.checkpoint_dir}")
    
    def register_provider(self, name: str, provider: callable):
        """Register a function that provides state data for a component."""
        self._state_providers[name] = provider
        logger.debug(f"Registered state provider: {name}")
    
    def register_restorer(self, name: str, restorer: callable):
        """Register a function that restores state for a component."""
        self._state_restorers[name] = restorer
        logger.debug(f"Registered state restorer: {name}")
    
    def create_snapshot(self) -> StateSnapshot:
        """Create a complete system state snapshot."""
        with self._lock:
            snapshot_data = {}
            
            for name, provider in self._state_providers.items():
                try:
                    state = provider()
                    if state is not None:
                        snapshot_data[name] = state
                        logger.debug(f"Captured state for: {name}")
                except Exception as e:
                    logger.error(f"Failed to capture state for {name}: {e}")
                    snapshot_data[name] = {"error": str(e)}
            
            return StateSnapshot(snapshot_data)
    
    def save_checkpoint(self, snapshot: StateSnapshot = None) -> str:
        """Save a checkpoint to disk."""
        if snapshot is None:
            snapshot = self.create_snapshot()
        
        timestamp_str = datetime.fromtimestamp(snapshot.timestamp).strftime("%Y%m%d_%H%M%S")
        checkpoint_file = self.checkpoint_dir / f"checkpoint_{timestamp_str}.json"
        
        try:
            with open(checkpoint_file, 'w') as f:
                json.dump(snapshot.to_dict(), f, indent=2)
            
            self._last_checkpoint_time = snapshot.timestamp
            logger.info(f"Checkpoint saved: {checkpoint_file}")
            
            # Cleanup old checkpoints
            self._cleanup_old_checkpoints()
            
            return str(checkpoint_file)
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
            raise
    
    def load_latest_checkpoint(self) -> Optional[StateSnapshot]:
        """Load the most recent checkpoint from disk."""
        checkpoint_files = sorted(
            self.checkpoint_dir.glob("checkpoint_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        if not checkpoint_files:
            logger.info("No checkpoints found")
            return None
        
        latest_file = checkpoint_files[0]
        try:
            with open(latest_file, 'r') as f:
                data = json.load(f)
            
            snapshot = StateSnapshot.from_dict(data)
            logger.info(f"Loaded checkpoint from: {latest_file}")
            return snapshot
        except Exception as e:
            logger.error(f"Failed to load checkpoint {latest_file}: {e}")
            return None
    
    def restore_from_checkpoint(self, snapshot: StateSnapshot = None) -> bool:
        """Restore system state from a checkpoint."""
        if snapshot is None:
            snapshot = self.load_latest_checkpoint()
        
        if snapshot is None:
            logger.warning("No snapshot available for restoration")
            return False
        
        success_count = 0
        fail_count = 0
        
        for component_name, state_data in snapshot.data.items():
            if "error" in state_data:
                logger.warning(f"Skipping {component_name} due to captured error")
                continue
            
            if component_name in self._state_restorers:
                try:
                    restorer = self._state_restorers[component_name]
                    restorer(state_data)
                    success_count += 1
                    logger.info(f"Restored state for: {component_name}")
                except Exception as e:
                    fail_count += 1
                    logger.error(f"Failed to restore {component_name}: {e}")
            else:
                logger.warning(f"No restorer registered for: {component_name}")
        
        logger.info(f"Restoration complete: {success_count} succeeded, {fail_count} failed")
        return fail_count == 0
    
    def _cleanup_old_checkpoints(self):
        """Remove old checkpoints beyond max_checkpoints limit."""
        checkpoint_files = sorted(
            self.checkpoint_dir.glob("checkpoint_*.json"),
            key=lambda p: p.stat().st_mtime
        )
        
        while len(checkpoint_files) > self.max_checkpoints:
            oldest = checkpoint_files.pop(0)
            try:
                oldest.unlink()
                logger.debug(f"Removed old checkpoint: {oldest}")
            except Exception as e:
                logger.error(f"Failed to remove old checkpoint {oldest}: {e}")
    
    def start_auto_save(self):
        """Start automatic checkpoint saving in background thread."""
        if self._auto_save_thread and self._auto_save_thread.is_alive():
            logger.warning("Auto-save already running")
            return
        
        self._stop_auto_save.clear()
        self._auto_save_thread = threading.Thread(target=self._auto_save_loop, daemon=True)
        self._auto_save_thread.start()
        logger.info(f"Auto-save started (interval: {self.auto_save_interval}s)")
    
    def stop_auto_save(self):
        """Stop automatic checkpoint saving."""
        self._stop_auto_save.set()
        if self._auto_save_thread:
            self._auto_save_thread.join(timeout=5)
            logger.info("Auto-save stopped")
    
    def _auto_save_loop(self):
        """Background loop for automatic checkpoint saving."""
        while not self._stop_auto_save.is_set():
            if self._stop_auto_save.wait(timeout=self.auto_save_interval):
                break
            
            try:
                self.save_checkpoint()
            except Exception as e:
                logger.error(f"Auto-save failed: {e}")
    
    def get_checkpoint_history(self) -> List[Dict[str, Any]]:
        """Get list of all available checkpoints."""
        checkpoints = []
        
        for checkpoint_file in sorted(
            self.checkpoint_dir.glob("checkpoint_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        ):
            try:
                stat = checkpoint_file.stat()
                checkpoints.append({
                    "file": str(checkpoint_file),
                    "size_bytes": stat.st_size,
                    "modified_time": stat.st_mtime,
                    "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
            except Exception as e:
                logger.error(f"Failed to read checkpoint info {checkpoint_file}: {e}")
        
        return checkpoints
    
    def get_stats(self) -> Dict[str, Any]:
        """Get checkpoint manager statistics."""
        return {
            "checkpoint_dir": str(self.checkpoint_dir),
            "max_checkpoints": self.max_checkpoints,
            "auto_save_interval": self.auto_save_interval,
            "last_checkpoint_time": self._last_checkpoint_time,
            "auto_save_running": self._auto_save_thread is not None and self._auto_save_thread.is_alive(),
            "registered_providers": list(self._state_providers.keys()),
            "registered_restorers": list(self._state_restorers.keys()),
            "available_checkpoints": len(self.get_checkpoint_history())
        }

# Global checkpoint manager instance
checkpoint_manager = CheckpointManager()

def get_checkpoint_manager() -> CheckpointManager:
    """Get the global checkpoint manager instance."""
    return checkpoint_manager

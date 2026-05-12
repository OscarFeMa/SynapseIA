"""
Degraded Mode Manager for Synapse Council.
Enables graceful degradation when critical services are unavailable.
"""
import threading
import time
from enum import Enum
from typing import Dict, List, Callable, Optional, Any
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)

class ServiceLevel(Enum):
    """Service availability levels."""
    FULL = "full"              # All features available
    DEGRADED = "degraded"      # Core features only
    MINIMAL = "minimal"        # Emergency operations only
    OFFLINE = "offline"        # No operations possible

@dataclass
class ServiceStatus:
    """Status of a specific service."""
    name: str
    available: bool
    last_check: float = field(default_factory=time.time)
    failure_count: int = 0
    last_error: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "available": self.available,
            "last_check": self.last_check,
            "failure_count": self.failure_count,
            "last_error": self.last_error
        }

class DegradedModeManager:
    """Manages graceful degradation of system functionality."""
    
    def __init__(self):
        self._services: Dict[str, ServiceStatus] = {}
        self._fallbacks: Dict[str, Callable] = {}
        self._service_dependencies: Dict[str, List[str]] = {}
        self._current_level = ServiceLevel.FULL
        self._level_callbacks: List[Callable[[ServiceLevel], None]] = []
        self._lock = threading.Lock()
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        
        logger.info("DegradedModeManager initialized")
    
    def register_service(
        self,
        name: str,
        critical: bool = False,
        dependencies: List[str] = None
    ):
        """Register a service for monitoring."""
        with self._lock:
            self._services[name] = ServiceStatus(name=name, available=True)
            if dependencies:
                self._service_dependencies[name] = dependencies
            
            level = "CRITICAL" if critical else "OPTIONAL"
            logger.info(f"Registered service: {name} ({level})")
    
    def set_service_status(
        self,
        name: str,
        available: bool,
        error: Optional[str] = None
    ):
        """Update the status of a service."""
        with self._lock:
            if name not in self._services:
                logger.warning(f"Unknown service: {name}")
                return
            
            service = self._services[name]
            service.available = available
            service.last_check = time.time()
            
            if not available:
                service.failure_count += 1
                service.last_error = error
                logger.warning(f"Service {name} is unavailable: {error}")
            else:
                # Reset failure count on recovery
                if service.failure_count > 0:
                    service.failure_count = max(0, service.failure_count - 1)
                service.last_error = None
                logger.info(f"Service {name} recovered")
            
            # Recalculate overall system level
            self._recalculate_service_level()
    
    def register_fallback(self, service_name: str, fallback_func: Callable):
        """Register a fallback function for a service."""
        self._fallbacks[service_name] = fallback_func
        logger.debug(f"Registered fallback for: {service_name}")
    
    def execute_with_fallback(
        self,
        service_name: str,
        primary_func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute primary function, fallback if service unavailable."""
        with self._lock:
            service = self._services.get(service_name)
            if service and not service.available:
                if service_name in self._fallbacks:
                    logger.info(f"Using fallback for {service_name}")
                    return self._fallbacks[service_name](*args, **kwargs)
                else:
                    raise RuntimeError(f"Service {service_name} unavailable and no fallback registered")
        
        try:
            return primary_func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Primary function failed for {service_name}: {e}")
            self.set_service_status(service_name, False, str(e))
            
            if service_name in self._fallbacks:
                logger.info(f"Using fallback after failure for {service_name}")
                return self._fallbacks[service_name](*args, **kwargs)
            
            raise
    
    def _recalculate_service_level(self):
        """Recalculate the overall system service level."""
        if not self._services:
            return
        
        total_services = len(self._services)
        available_services = sum(1 for s in self._services.values() if s.available)
        
        # Check for critical service failures
        critical_failed = any(
            not s.available 
            for name, s in self._services.items()
            if self._is_critical(name)
        )
        
        availability_ratio = available_services / total_services if total_services > 0 else 0
        
        old_level = self._current_level
        
        if critical_failed or availability_ratio < 0.3:
            self._current_level = ServiceLevel.MINIMAL
        elif availability_ratio < 0.7:
            self._current_level = ServiceLevel.DEGRADED
        elif availability_ratio == 1.0:
            self._current_level = ServiceLevel.FULL
        else:
            self._current_level = ServiceLevel.DEGRADED
        
        if old_level != self._current_level:
            logger.warning(f"Service level changed: {old_level.value} -> {self._current_level.value}")
            self._notify_level_change(self._current_level)
    
    def _is_critical(self, service_name: str) -> bool:
        """Check if a service is critical."""
        # For now, consider services with dependencies as critical
        # This can be enhanced with explicit critical flags
        return any(
            service_name in deps 
            for deps in self._service_dependencies.values()
        )
    
    def _notify_level_change(self, new_level: ServiceLevel):
        """Notify callbacks of service level change."""
        for callback in self._level_callbacks:
            try:
                callback(new_level)
            except Exception as e:
                logger.error(f"Level callback failed: {e}")
    
    def on_level_change(self, callback: Callable[[ServiceLevel], None]):
        """Register a callback for service level changes."""
        self._level_callbacks.append(callback)
    
    @property
    def current_level(self) -> ServiceLevel:
        """Get current service level."""
        return self._current_level
    
    def is_available(self, feature_level: ServiceLevel) -> bool:
        """Check if a feature level is currently available."""
        level_order = [ServiceLevel.OFFLINE, ServiceLevel.MINIMAL, 
                      ServiceLevel.DEGRADED, ServiceLevel.FULL]
        
        current_idx = level_order.index(self._current_level)
        required_idx = level_order.index(feature_level)
        
        return current_idx >= required_idx
    
    def get_enabled_features(self) -> List[str]:
        """Get list of features enabled at current service level."""
        features = {
            ServiceLevel.FULL: [
                "task_queue", "real_time_monitoring", "auto_scaling",
                "checkpointing", "advanced_analytics", "multi_worker"
            ],
            ServiceLevel.DEGRADED: [
                "task_queue", "basic_monitoring", "checkpointing"
            ],
            ServiceLevel.MINIMAL: [
                "basic_task_execution", "emergency_logging"
            ],
            ServiceLevel.OFFLINE: []
        }
        
        return features.get(self._current_level, [])
    
    def get_all_services_status(self) -> Dict[str, dict]:
        """Get status of all registered services."""
        with self._lock:
            return {name: svc.to_dict() for name, svc in self._services.items()}
    
    def start_monitoring(self, check_interval: float = 30.0):
        """Start background service monitoring."""
        if self._monitoring:
            logger.warning("Monitoring already running")
            return
        
        self._monitoring = True
        
        def monitor_loop():
            while self._monitoring:
                # Perform health checks on services
                # This is a placeholder - actual implementation would check each service
                time.sleep(check_interval)
        
        self._monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self._monitor_thread.start()
        logger.info(f"Service monitoring started (interval: {check_interval}s)")
    
    def stop_monitoring(self):
        """Stop background service monitoring."""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
            logger.info("Service monitoring stopped")
    
    def get_stats(self) -> dict:
        """Get degraded mode manager statistics."""
        with self._lock:
            return {
                "current_level": self._current_level.value,
                "total_services": len(self._services),
                "available_services": sum(1 for s in self._services.values() if s.available),
                "enabled_features": self.get_enabled_features(),
                "services": self.get_all_services_status()
            }

# Global degraded mode manager instance
degraded_mode_manager = DegradedModeManager()

def get_degraded_mode_manager() -> DegradedModeManager:
    """Get the global degraded mode manager instance."""
    return degraded_mode_manager

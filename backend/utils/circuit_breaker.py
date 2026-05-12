"""
Circuit Breaker Pattern Implementation for Synapse Council.
Prevents cascading failures when external services are unavailable.
"""
import time
import threading
from enum import Enum
from typing import Callable, Any, Optional
from functools import wraps
import logging

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open" # Testing if service recovered

class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open."""
    pass

class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_max_calls: int = 3,
        name: str = "default"
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._half_open_calls = 0
        self._lock = threading.Lock()
        
    @property
    def state(self) -> CircuitState:
        with self._lock:
            if self._state == CircuitState.OPEN:
                if self._last_failure_time and \
                   time.time() - self._last_failure_time > self.recovery_timeout:
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
                    logger.info(f"Circuit '{self.name}' moved to HALF_OPEN")
            return self._state
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        current_state = self.state
        
        if current_state == CircuitState.OPEN:
            logger.warning(f"Circuit '{self.name}' is OPEN. Request rejected.")
            raise CircuitBreakerError(f"Circuit breaker '{self.name}' is open")
        
        if current_state == CircuitState.HALF_OPEN:
            if self._half_open_calls >= self.half_open_max_calls:
                logger.warning(f"Circuit '{self.name}' HALF_OPEN limit reached.")
                raise CircuitBreakerError(f"Circuit breaker '{self.name}' half-open limit exceeded")
            self._half_open_calls += 1
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.half_open_max_calls:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    self._success_count = 0
                    logger.info(f"Circuit '{self.name}' moved to CLOSED (recovered)")
            else:
                self._failure_count = 0
    
    def _on_failure(self):
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            
            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
                logger.warning(f"Circuit '{self.name}' moved to OPEN (recovery failed)")
            elif self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
                logger.error(f"Circuit '{self.name}' moved to OPEN (threshold exceeded)")
    
    def reset(self):
        """Manually reset the circuit breaker."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._last_failure_time = None
            self._half_open_calls = 0
            logger.info(f"Circuit '{self.name}' manually reset")
    
    def get_stats(self) -> dict:
        """Get current circuit breaker statistics."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "last_failure_time": self._last_failure_time,
            "threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout
        }

def circuit_breaker(
    failure_threshold: int = 5,
    recovery_timeout: float = 30.0,
    name: str = "default"
):
    """Decorator for circuit breaker pattern."""
    breaker = CircuitBreaker(
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout,
        name=name
    )
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return breaker.call(func, *args, **kwargs)
        wrapper.circuit_breaker = breaker
        return wrapper
    return decorator

# Global circuit breakers for critical components
circuit_breakers = {
    "worker_communication": CircuitBreaker(
        name="worker_communication",
        failure_threshold=3,
        recovery_timeout=15.0
    ),
    "database": CircuitBreaker(
        name="database",
        failure_threshold=5,
        recovery_timeout=30.0
    ),
    "external_api": CircuitBreaker(
        name="external_api",
        failure_threshold=3,
        recovery_timeout=60.0
    ),
    "file_system": CircuitBreaker(
        name="file_system",
        failure_threshold=5,
        recovery_timeout=10.0
    )
}

def get_circuit_breaker(name: str) -> CircuitBreaker:
    """Get or create a circuit breaker by name."""
    if name not in circuit_breakers:
        circuit_breakers[name] = CircuitBreaker(name=name)
    return circuit_breakers[name]

def get_all_circuit_stats() -> dict:
    """Get statistics for all circuit breakers."""
    return {name: cb.get_stats() for name, cb in circuit_breakers.items()}

"""
Synapse Council v2.1 - Sistema de Alertas Proactivas
Detección temprana de problemas y notificaciones automáticas
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from dataclasses import dataclass, field
import structlog

from backend.monitoring.metrics import get_metrics_collector, connected_workers, active_debates

logger = structlog.get_logger()


class AlertSeverity(Enum):
    """Niveles de severidad de alertas"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class AlertType(Enum):
    """Tipos de alertas del sistema"""
    WORKER_DOWN = "worker_down"
    WORKER_UNHEALTHY = "worker_unhealthy"
    HIGH_LATENCY = "high_latency"
    MEMORY_HIGH = "memory_high"
    CPU_HIGH = "cpu_high"
    DEBATE_FAILURE_SPIKE = "debate_failure_spike"
    CACHE_DISCONNECTED = "cache_disconnected"
    HEARTBEAT_LOST = "heartbeat_lost"
    QUEUE_BACKPRESSURE = "queue_backpressure"
    SYSTEM_RECOVERING = "system_recovering"


@dataclass
class Alert:
    """Estructura de alerta"""
    alert_type: AlertType
    severity: AlertSeverity
    message: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    source: str = "synapse_system"
    details: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte alerta a diccionario"""
        return {
            "type": self.alert_type.value,
            "severity": self.severity.value,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "details": self.details,
            "resolved": self.resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None
        }


class AlertManager:
    """Gestor centralizado de alertas"""
    
    def __init__(self):
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.callbacks: Dict[AlertType, List[Callable]] = {}
        self.thresholds = {
            "worker_healthy_min": 1,
            "latency_warning_ms": 5000,
            "latency_critical_ms": 15000,
            "memory_warning_percent": 80,
            "memory_critical_percent": 95,
            "cpu_warning_percent": 80,
            "cpu_critical_percent": 95,
            "debate_failure_rate_warning": 0.1,
            "debate_failure_rate_critical": 0.3,
            "heartbeat_timeout_seconds": 30
        }
        
    def register_callback(self, alert_type: AlertType, callback: Callable):
        """Registra callback para tipo de alerta"""
        if alert_type not in self.callbacks:
            self.callbacks[alert_type] = []
        self.callbacks[alert_type].append(callback)
    
    async def create_alert(
        self,
        alert_type: AlertType,
        severity: AlertSeverity,
        message: str,
        details: Dict[str, Any] = None
    ):
        """Crea una nueva alerta"""
        alert_id = f"{alert_type.value}_{datetime.utcnow().timestamp()}"
        
        alert = Alert(
            alert_type=alert_type,
            severity=severity,
            message=message,
            details=details or {},
            source="synapse_alert_manager"
        )
        
        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)
        
        logger.warning(
            "alert.created",
            alert_id=alert_id,
            type=alert_type.value,
            severity=severity.value,
            message=message
        )
        
        # Notificar callbacks registrados
        if alert_type in self.callbacks:
            for callback in self.callbacks[alert_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(alert)
                    else:
                        callback(alert)
                except Exception as e:
                    logger.error("alert.callback_error", error=str(e))
        
        return alert_id
    
    async def resolve_alert(self, alert_id: str):
        """Resuelve una alerta activa"""
        if alert_id not in self.active_alerts:
            return False
        
        alert = self.active_alerts[alert_id]
        alert.resolved = True
        alert.resolved_at = datetime.utcnow()
        
        del self.active_alerts[alert_id]
        
        logger.info(
            "alert.resolved",
            alert_id=alert_id,
            type=alert.alert_type.value
        )
        
        return True
    
    def get_active_alerts(self, severity: Optional[AlertSeverity] = None) -> List[Alert]:
        """Obtiene alertas activas, opcionalmente filtradas por severidad"""
        alerts = list(self.active_alerts.values())
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        return alerts
    
    def get_alert_history(
        self,
        limit: int = 100,
        start_time: Optional[datetime] = None
    ) -> List[Alert]:
        """Obtiene histórico de alertas"""
        history = self.alert_history[-limit:]
        if start_time:
            history = [a for a in history if a.timestamp >= start_time]
        return history
    
    def clear_resolved(self, older_than: timedelta = timedelta(hours=1)):
        """Limpia alertas resueltas antiguas"""
        cutoff = datetime.utcnow() - older_than
        self.alert_history = [
            a for a in self.alert_history
            if not a.resolved or a.resolved_at is None or a.resolved_at > cutoff
        ]


class HealthMonitor:
    """Monitor de salud del sistema con detección proactiva"""
    
    def __init__(self, alert_manager: AlertManager):
        self.alert_manager = alert_manager
        self.metrics_collector = get_metrics_collector()
        self.running = False
        self.check_interval = 10  # segundos
        
        # Estado previo para detectar cambios
        self.prev_worker_count = 0
        self.prev_latencies: Dict[str, float] = {}
        self.consecutive_failures: Dict[str, int] = {}
        
    async def start(self):
        """Inicia el monitor de salud"""
        self.running = True
        logger.info("health_monitor.started", check_interval=self.check_interval)
        
        while self.running:
            try:
                await self._run_health_checks()
            except Exception as e:
                logger.error("health_monitor.check_error", error=str(e))
            
            await asyncio.sleep(self.check_interval)
    
    async def stop(self):
        """Detiene el monitor de salud"""
        self.running = False
        logger.info("health_monitor.stopped")
    
    async def _run_health_checks(self):
        """Ejecuta todos los checks de salud"""
        await self._check_workers()
        await self._check_system_resources()
        await self._check_debate_health()
        await self._check_cache()
    
    async def _check_workers(self):
        """Verifica salud de workers"""
        try:
            from backend.services.worker_pool import get_worker_pool
            worker_pool = get_worker_pool()
            status = await worker_pool.get_pool_status()
            
            current_count = status.get("connected_workers", 0)
            healthy_count = status.get("healthy_workers", 0)
            
            # Detectar caída de workers
            if current_count < self.prev_worker_count and current_count < self.threshold("worker_healthy_min"):
                await self.alert_manager.create_alert(
                    AlertType.WORKER_DOWN,
                    AlertSeverity.CRITICAL,
                    f"Worker desconectado. Total: {current_count}, Saludables: {healthy_count}",
                    {"previous_count": self.prev_worker_count, "current_count": current_count}
                )
            
            # Detectar workers no saludables
            if healthy_count == 0 and current_count > 0:
                await self.alert_manager.create_alert(
                    AlertType.WORKER_UNHEALTHY,
                    AlertSeverity.WARNING,
                    f"{current_count} workers conectados pero ninguno saludable",
                    {"connected": current_count, "healthy": healthy_count}
                )
            
            # Detectar recuperación
            if current_count > self.prev_worker_count and self.prev_worker_count < self.threshold("worker_healthy_min"):
                await self.alert_manager.create_alert(
                    AlertType.SYSTEM_RECOVERING,
                    AlertSeverity.INFO,
                    f"Sistema recuperándose. Workers: {current_count}",
                    {"previous_count": self.prev_worker_count, "current_count": current_count}
                )
            
            self.prev_worker_count = current_count
            
        except Exception as e:
            logger.error("health_monitor.worker_check_error", error=str(e))
    
    async def _check_system_resources(self):
        """Verifica recursos del sistema (CPU, memoria)"""
        try:
            import psutil
            
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Check CPU
            if cpu_percent >= self.threshold("cpu_critical_percent"):
                await self._alert_resource("CPU", cpu_percent, AlertSeverity.CRITICAL)
            elif cpu_percent >= self.threshold("cpu_warning_percent"):
                await self._alert_resource("CPU", cpu_percent, AlertSeverity.WARNING)
            
            # Check Memoria
            if memory_percent >= self.threshold("memory_critical_percent"):
                await self._alert_resource("Memoria", memory_percent, AlertSeverity.CRITICAL)
            elif memory_percent >= self.threshold("memory_warning_percent"):
                await self._alert_resource("Memoria", memory_percent, AlertSeverity.WARNING)
                
        except ImportError:
            pass  # psutil no disponible
        except Exception as e:
            logger.error("health_monitor.resource_check_error", error=str(e))
    
    async def _alert_resource(self, resource: str, value: float, severity: AlertSeverity):
        """Crea alerta de recurso"""
        alert_key = f"{resource.lower()}_{severity.value}"
        
        # Evitar alertas duplicadas
        if alert_key not in self.alert_manager.active_alerts:
            await self.alert_manager.create_alert(
                AlertType.CPU_HIGH if resource == "CPU" else AlertType.MEMORY_HIGH,
                severity,
                f"{resource} en {value:.1f}% - Umbral {severity.value} superado",
                {"resource": resource, "value": value, "threshold": self.threshold(f"{resource.lower()}_warning_percent")}
            )
    
    async def _check_debate_health(self):
        """Verifica salud de debates (tasa de fallos)"""
        try:
            metrics_summary = self.metrics_collector.get_metrics_summary()
            
            # Calcular tasa de fallos (simplificado)
            total = metrics_summary.get("debates_total", 0)
            if total > 0:
                # En implementación real, obtener fallos de métricas detalladas
                failure_rate = metrics_summary.get("failure_rate", 0)
                
                if failure_rate >= self.threshold("debate_failure_rate_critical"):
                    await self.alert_manager.create_alert(
                        AlertType.DEBATE_FAILURE_SPIKE,
                        AlertSeverity.CRITICAL,
                        f"Tasa de fallos crítica: {failure_rate:.1%}",
                        {"failure_rate": failure_rate, "total_debates": total}
                    )
                elif failure_rate >= self.threshold("debate_failure_rate_warning"):
                    await self.alert_manager.create_alert(
                        AlertType.DEBATE_FAILURE_SPIKE,
                        AlertSeverity.WARNING,
                        f"Tasa de fallos elevada: {failure_rate:.1%}",
                        {"failure_rate": failure_rate, "total_debates": total}
                    )
                    
        except Exception as e:
            logger.error("health_monitor.debate_check_error", error=str(e))
    
    async def _check_cache(self):
        """Verifica conexión con caché"""
        try:
            from backend.services.cache_service import get_cache_service
            cache_service = get_cache_service()
            status = await cache_service.get_health_status()
            
            if status.get("status") == "disconnected":
                await self.alert_manager.create_alert(
                    AlertType.CACHE_DISCONNECTED,
                    AlertSeverity.WARNING,
                    "Servicio de caché desconectado",
                    {"cache_status": status}
                )
                
        except Exception as e:
            logger.error("health_monitor.cache_check_error", error=str(e))
    
    def threshold(self, key: str) -> float:
        """Obtiene valor de umbral"""
        return self.alert_manager.thresholds.get(key, 0)


# Singleton instances
_alert_manager: Optional[AlertManager] = None
_health_monitor: Optional[HealthMonitor] = None


def get_alert_manager() -> AlertManager:
    """Obtiene instancia singleton del gestor de alertas"""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
    return _alert_manager


def get_health_monitor() -> Optional[HealthMonitor]:
    """Obtiene instancia del monitor de salud"""
    global _health_monitor
    return _health_monitor


async def init_health_monitoring():
    """Inicializa el sistema de monitoreo de salud"""
    global _health_monitor
    
    alert_manager = get_alert_manager()
    _health_monitor = HealthMonitor(alert_manager)
    
    logger.info("health_monitoring.initialized")
    
    # Iniciar monitor en background
    asyncio.create_task(_health_monitor.start())
    
    return _health_monitor


async def shutdown_health_monitoring():
    """Detiene el sistema de monitoreo"""
    global _health_monitor
    
    if _health_monitor:
        await _health_monitor.stop()
        logger.info("health_monitoring.shutdown")

"""
Synapse Council v2.0 - Prometheus Metrics
Métricas para monitoreo operativo del sistema
"""
import time
from typing import Dict, Any
from prometheus_client import Counter, Histogram, Gauge, Info, CollectorRegistry, generate_latest
import structlog

logger = structlog.get_logger()

# Registry para métricas
registry = CollectorRegistry()

# ─── Contadores ─────────────────────────────────────────────
debates_total = Counter(
    'synapse_debates_total',
    'Total number of debates created',
    ['mode', 'status'],
    registry=registry
)

debates_completed = Counter(
    'synapse_debates_completed_total',
    'Total number of debates completed',
    ['mode', 'duration_category'],
    registry=registry
)

debates_failed = Counter(
    'synapse_debates_failed_total',
    'Total number of debates failed',
    ['mode', 'error_type'],
    registry=registry
)

agent_calls_total = Counter(
    'synapse_agent_calls_total',
    'Total number of agent calls',
    ['agent_role', 'provider', 'node', 'status'],
    registry=registry
)

tokens_generated = Counter(
    'synapse_tokens_generated_total',
    'Total number of tokens generated',
    ['agent_role', 'provider', 'model'],
    registry=registry
)

# ─── Histogramas ───────────────────────────────────────────
debate_duration = Histogram(
    'synapse_debate_duration_seconds',
    'Time spent processing debates',
    ['mode'],
    buckets=[5, 10, 30, 60, 120, 300, 600, 1800],
    registry=registry
)

agent_latency = Histogram(
    'synapse_agent_latency_seconds',
    'Agent response latency',
    ['agent_role', 'provider', 'model', 'node'],
    buckets=[0.1, 0.5, 1, 2, 5, 10, 30, 60],
    registry=registry
)

# ─── Gauges ───────────────────────────────────────────────
active_debates = Gauge(
    'synapse_active_debates',
    'Number of currently active debates',
    registry=registry
)

connected_workers = Gauge(
    'synapse_connected_workers',
    'Number of connected workers',
    registry=registry
)

system_memory_usage = Gauge(
    'synapse_memory_usage_bytes',
    'Memory usage in bytes',
    registry=registry
)

system_cpu_usage = Gauge(
    'synapse_cpu_usage_percent',
    'CPU usage percentage',
    registry=registry
)

ollama_models_loaded = Gauge(
    'synapse_ollama_models_loaded',
    'Number of Ollama models loaded',
    registry=registry
)

# ─── Info ───────────────────────────────────────────────────
build_info = Info(
    'synapse_build_info',
    'Build information',
    registry=registry
)


class MetricsCollector:
    """Colector de métricas centralizado"""
    
    def __init__(self):
        self.start_time = time.time()
        
    def record_debate_start(self, mode: str, debate_id: str):
        """Registra inicio de debate"""
        debates_total.labels(mode=mode, status='started').inc()
        active_debates.inc()
        logger.info("metrics.debate_started", debate_id=debate_id, mode=mode)
    
    def record_debate_complete(self, mode: str, duration: float, debate_id: str):
        """Registra debate completado"""
        debates_completed.labels(mode=mode, duration_category=self._categorize_duration(duration)).inc()
        debate_duration.labels(mode=mode).observe(duration)
        active_debates.dec()
        
        # Categorizar duración
        logger.info("metrics.debate_completed", 
                  debate_id=debate_id, 
                  mode=mode, 
                  duration=duration,
                  category=self._categorize_duration(duration))
    
    def record_debate_failed(self, mode: str, error_type: str, debate_id: str):
        """Registra debate fallido"""
        debates_failed.labels(mode=mode, error_type=error_type).inc()
        active_debates.dec()
        logger.info("metrics.debate_failed", debate_id=debate_id, mode=mode, error_type=error_type)
    
    def record_agent_call(self, agent_role: str, provider: str, node: str, 
                       status: str, latency: float, tokens: int, model: str):
        """Registra llamada a agente"""
        agent_calls_total.labels(
            agent_role=agent_role, 
            provider=provider, 
            node=node, 
            status=status
        ).inc()
        
        if status == 'success':
            agent_latency.labels(
                agent_role=agent_role, 
                provider=provider, 
                model=model, 
                node=node
            ).observe(latency)
            tokens_generated.labels(
                agent_role=agent_role, 
                provider=provider, 
                model=model
            ).inc(tokens)
        
        logger.debug("metrics.agent_call", 
                   agent_role=agent_role, 
                   provider=provider, 
                   node=node, 
                   status=status, 
                   latency=latency, 
                   tokens=tokens)
    
    def update_worker_count(self, count: int):
        """Actualiza número de workers conectados"""
        connected_workers.set(count)
        logger.debug("metrics.workers_updated", count=count)
    
    def update_system_metrics(self, memory_bytes: int, cpu_percent: float):
        """Actualiza métricas del sistema"""
        system_memory_usage.set(memory_bytes)
        system_cpu_usage.set(cpu_percent)
    
    def update_ollama_models(self, count: int):
        """Actualiza número de modelos Ollama cargados"""
        ollama_models_loaded.set(count)
    
    def set_build_info(self, version: str, commit: str = "", build_time: str = ""):
        """Establece información de build"""
        build_info.info({
            'version': version,
            'commit': commit,
            'build_time': build_time
        })
    
    def _categorize_duration(self, duration: float) -> str:
        """Categoriza duración del debate"""
        if duration < 30:
            return 'fast'
        elif duration < 120:
            return 'normal'
        elif duration < 300:
            return 'slow'
        else:
            return 'very_slow'
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Obtiene resumen de métricas actuales"""
        return {
            'debates_total': debates_total._value._value,
            'active_debates': active_debates._value._value,
            'connected_workers': connected_workers._value._value,
            'uptime_seconds': time.time() - self.start_time
        }


# Singleton instance
_metrics_collector: MetricsCollector = None


def get_metrics_collector() -> MetricsCollector:
    """Obtiene instancia singleton del colector"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def get_prometheus_metrics() -> str:
    """Genera métricas en formato Prometheus"""
    return generate_latest(registry).decode('utf-8')

"""
Synapse Council v2.0 - Worker Pool Manager
Gestión de múltiples workers con load balancing
"""
import asyncio
import random
import time
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import structlog

from backend.monitoring.metrics import get_metrics_collector
from backend.services.cache_service import get_cache_service

logger = structlog.get_logger()


class LoadBalancingStrategy(Enum):
    """Estrategias de balanceo de carga"""
    ROUND_ROBIN = "round_robin"
    LEAST_LOADED = "least_loaded"
    RANDOM = "random"
    WEIGHTED = "weighted"


class WorkerInfo:
    """Información de un worker"""
    
    def __init__(self, worker_id: str, host: str, port: int, 
                 max_concurrent: int = 5, weight: int = 1):
        self.worker_id = worker_id
        self.host = host
        self.port = port
        self.max_concurrent = max_concurrent
        self.weight = weight
        self.current_load = 0
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.last_heartbeat = time.time()
        self.is_healthy = True
        self.response_times = []  # Últimos 50 tiempos de respuesta
        self.lock = asyncio.Lock()
    
    async def acquire(self) -> bool:
        """Intenta adquirir este worker"""
        async with self.lock:
            if self.current_load < self.max_concurrent and self.is_healthy:
                self.current_load += 1
                self.total_requests += 1
                return True
            return False
    
    async def release(self, success: bool = True, response_time: float = 0):
        """Libera este worker"""
        async with self.lock:
            self.current_load = max(0, self.current_load - 1)
            
            if success:
                self.successful_requests += 1
                # Mantener solo últimos 50 tiempos
                self.response_times.append(response_time)
                if len(self.response_times) > 50:
                    self.response_times.pop(0)
            else:
                self.failed_requests += 1
    
    def get_load_percentage(self) -> float:
        """Obtiene porcentaje de carga"""
        return (self.current_load / self.max_concurrent) * 100
    
    def get_success_rate(self) -> float:
        """Obtiene tasa de éxito"""
        if self.total_requests == 0:
            return 100.0
        return (self.successful_requests / self.total_requests) * 100
    
    def get_avg_response_time(self) -> float:
        """Obtiene tiempo de respuesta promedio"""
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)
    
    def update_heartbeat(self):
        """Actualiza timestamp de heartbeat"""
        self.last_heartbeat = time.time()
        self.is_healthy = True
    
    def check_health(self, timeout: float = 30.0) -> bool:
        """Verifica si worker está saludable"""
        time_since_heartbeat = time.time() - self.last_heartbeat
        if time_since_heartbeat > timeout:
            self.is_healthy = False
            return False
        return self.is_healthy


class WorkerPool:
    """Pool de workers con load balancing"""
    
    def __init__(self, strategy: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN):
        self.workers: Dict[str, WorkerInfo] = {}
        self.strategy = strategy
        self.round_robin_index = 0
        self.metrics = get_metrics_collector()
        self.cache = get_cache_service()
        self.health_check_interval = 30  # segundos
        self.health_check_task: Optional[asyncio.Task] = None
        self.lock = asyncio.Lock()
        
    async def start(self):
        """Inicia el pool y health checks"""
        if self.health_check_task is None:
            self.health_check_task = asyncio.create_task(self._health_check_loop())
            logger.info("worker_pool.started", strategy=self.strategy.value)
    
    async def stop(self):
        """Detiene el pool"""
        if self.health_check_task:
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass
        logger.info("worker_pool.stopped")
    
    async def add_worker(self, worker_id: str, host: str, port: int, 
                       max_concurrent: int = 5, weight: int = 1) -> bool:
        """Agrega un worker al pool"""
        async with self.lock:
            if worker_id in self.workers:
                logger.warning("worker_pool.worker_exists", worker_id=worker_id)
                return False
            
            worker = WorkerInfo(worker_id, host, port, max_concurrent, weight)
            worker.update_heartbeat()  # Marcar como saludable inicialmente
            self.workers[worker_id] = worker
            
            logger.info("worker_pool.worker_added", 
                       worker_id=worker_id, 
                       host=host, 
                       port=port,
                       max_concurrent=max_concurrent,
                       weight=weight)
            
            # Actualizar métricas
            self.metrics.update_worker_count(len(self.workers))
            return True
    
    async def remove_worker(self, worker_id: str) -> bool:
        """Remueve un worker del pool"""
        async with self.lock:
            if worker_id not in self.workers:
                logger.warning("worker_pool.worker_not_found", worker_id=worker_id)
                return False
            
            del self.workers[worker_id]
            logger.info("worker_pool.worker_removed", worker_id=worker_id)
            
            # Actualizar métricas
            self.metrics.update_worker_count(len(self.workers))
            return True
    
    async def select_worker(self, strategy: Optional[LoadBalancingStrategy] = None) -> Optional[WorkerInfo]:
        """Selecciona worker según estrategia"""
        if not self.workers:
            logger.warning("worker_pool.no_workers")
            return None
        
        # Filtrar workers saludables y con capacidad
        available_workers = [
            w for w in self.workers.values() 
            if w.is_healthy and w.current_load < w.max_concurrent
        ]
        
        if not available_workers:
            logger.warning("worker_pool.no_available_workers")
            return None
        
        strategy = strategy or self.strategy
        
        if strategy == LoadBalancingStrategy.ROUND_ROBIN:
            worker = await self._select_round_robin(available_workers)
        elif strategy == LoadBalancingStrategy.LEAST_LOADED:
            worker = await self._select_least_loaded(available_workers)
        elif strategy == LoadBalancingStrategy.RANDOM:
            worker = await self._select_random(available_workers)
        elif strategy == LoadBalancingStrategy.WEIGHTED:
            worker = await self._select_weighted(available_workers)
        else:
            worker = available_workers[0]
        
        return worker
    
    async def _select_round_robin(self, workers: List[WorkerInfo]) -> WorkerInfo:
        """Selección Round Robin"""
        worker = workers[self.round_robin_index % len(workers)]
        self.round_robin_index += 1
        return worker
    
    async def _select_least_loaded(self, workers: List[WorkerInfo]) -> WorkerInfo:
        """Selección por menor carga"""
        return min(workers, key=lambda w: w.current_load)
    
    async def _select_random(self, workers: List[WorkerInfo]) -> WorkerInfo:
        """Selección aleatoria"""
        return random.choice(workers)
    
    async def _select_weighted(self, workers: List[WorkerInfo]) -> WorkerInfo:
        """Selección ponderada por peso"""
        total_weight = sum(w.weight for w in workers)
        if total_weight == 0:
            return workers[0]
        
        r = random.uniform(0, total_weight)
        current_weight = 0
        
        for worker in workers:
            current_weight += worker.weight
            if r <= current_weight:
                return worker
        
        return workers[-1]
    
    async def execute_on_worker(self, worker_id: str, operation: Callable, 
                               *args, **kwargs) -> Any:
        """Ejecuta operación en worker específico"""
        if worker_id not in self.workers:
            raise ValueError(f"Worker {worker_id} not found")
        
        worker = self.workers[worker_id]
        
        # Intentar adquirir worker
        if not await worker.acquire():
            raise RuntimeError(f"Worker {worker_id} is at full capacity")
        
        start_time = time.time()
        success = False
        
        try:
            result = await operation(worker, *args, **kwargs)
            success = True
            return result
        except Exception as e:
            logger.error("worker_pool.operation_failed", 
                       worker_id=worker_id, 
                       error=str(e))
            raise
        finally:
            response_time = time.time() - start_time
            await worker.release(success, response_time)
    
    async def get_pool_status(self) -> Dict[str, Any]:
        """Obtiene estado completo del pool"""
        workers_status = []
        
        for worker_id, worker in self.workers.items():
            workers_status.append({
                'worker_id': worker_id,
                'host': worker.host,
                'port': worker.port,
                'current_load': worker.current_load,
                'max_concurrent': worker.max_concurrent,
                'load_percentage': worker.get_load_percentage(),
                'total_requests': worker.total_requests,
                'success_rate': worker.get_success_rate(),
                'avg_response_time': worker.get_avg_response_time(),
                'is_healthy': worker.is_healthy,
                'last_heartbeat': worker.last_heartbeat
            })
        
        total_capacity = sum(w.max_concurrent for w in self.workers.values())
        current_load = sum(w.current_load for w in self.workers.values())
        
        return {
            'strategy': self.strategy.value,
            'total_workers': len(self.workers),
            'healthy_workers': len([w for w in self.workers.values() if w.is_healthy]),
            'total_capacity': total_capacity,
            'current_load': current_load,
            'pool_utilization': (current_load / total_capacity * 100) if total_capacity > 0 else 0,
            'workers': workers_status
        }
    
    async def _health_check_loop(self):
        """Bucle de verificación de salud"""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                
                unhealthy_workers = []
                for worker_id, worker in self.workers.items():
                    if not worker.check_health():
                        unhealthy_workers.append(worker_id)
                
                if unhealthy_workers:
                    logger.warning("worker_pool.unhealthy_workers", 
                               workers=unhealthy_workers)
                
                # Actualizar métricas
                healthy_count = len([w for w in self.workers.values() if w.is_healthy])
                self.metrics.update_worker_count(healthy_count)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("worker_pool.health_check_error", error=str(e))
    
    async def update_worker_heartbeat(self, worker_id: str):
        """Actualiza heartbeat de worker específico"""
        if worker_id in self.workers:
            self.workers[worker_id].update_heartbeat()
            logger.debug("worker_pool.heartbeat_updated", worker_id=worker_id)
    
    def set_strategy(self, strategy: LoadBalancingStrategy):
        """Cambia estrategia de balanceo"""
        self.strategy = strategy
        logger.info("worker_pool.strategy_changed", new_strategy=strategy.value)


# Singleton instance
_worker_pool: Optional[WorkerPool] = None


def get_worker_pool() -> WorkerPool:
    """Obtiene instancia singleton del pool"""
    global _worker_pool
    if _worker_pool is None:
        _worker_pool = WorkerPool()
    return _worker_pool

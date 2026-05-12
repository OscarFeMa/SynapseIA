"""
Synapse Council v2.1 - Task Queue Service
Cola de tareas persistente con Redis/SQLite, priorización y backpressure
"""
import asyncio
import json
import time
import sqlite3
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass, asdict
from datetime import datetime
import structlog
import threading
from pathlib import Path

logger = structlog.get_logger()


class TaskPriority(Enum):
    """Prioridades de tareas"""
    CRITICAL = 0  # Máxima prioridad
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4


class TaskStatus(Enum):
    """Estados de una tarea"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


@dataclass
class Task:
    """Representación de una tarea en la cola"""
    task_id: str
    task_type: str
    payload: Dict[str, Any]
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    created_at: float = 0.0
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    worker_id: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None
    result: Optional[Any] = None
    timeout: Optional[float] = None  # Timeout en segundos
    
    def __post_init__(self):
        if self.created_at == 0.0:
            self.created_at = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario serializable"""
        data = asdict(self)
        data['priority'] = self.priority.value
        data['status'] = self.status.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Crea instancia desde diccionario"""
        data = data.copy()
        data['priority'] = TaskPriority(data['priority'])
        data['status'] = TaskStatus(data['status'])
        return cls(**data)
    
    def is_expired(self) -> bool:
        """Verifica si la tarea ha expirado"""
        if self.timeout is None:
            return False
        return (time.time() - self.created_at) > self.timeout


class TaskQueueBackend:
    """Interfaz base para backends de cola"""
    
    async def enqueue(self, task: Task) -> bool:
        raise NotImplementedError
    
    async def dequeue(self, priorities: Optional[List[TaskPriority]] = None) -> Optional[Task]:
        raise NotImplementedError
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        raise NotImplementedError
    
    async def update_task(self, task: Task) -> bool:
        raise NotImplementedError
    
    async def remove_task(self, task_id: str) -> bool:
        raise NotImplementedError
    
    async def get_queue_size(self) -> int:
        raise NotImplementedError
    
    async def clear(self) -> bool:
        raise NotImplementedError


class SQLiteTaskQueue(TaskQueueBackend):
    """Implementación SQLite para persistencia de cola"""
    
    def __init__(self, db_path: str = "synapse_tasks.db"):
        self.db_path = Path(db_path)
        self._lock = threading.Lock()
        self._init_db()
        logger.info("task_queue.sqlite_initialized", path=str(self.db_path))
    
    def _init_db(self):
        """Inicializa base de datos"""
        with self._lock:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    task_type TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    priority INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    started_at REAL,
                    completed_at REAL,
                    worker_id TEXT,
                    retry_count INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 3,
                    error_message TEXT,
                    result TEXT,
                    timeout REAL
                )
            ''')
            
            # Índice para búsqueda por prioridad y estado
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_priority_status 
                ON tasks(priority, status)
                WHERE status IN ('pending', 'queued', 'retrying')
            ''')
            
            # Índice para búsqueda por task_id
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_task_id 
                ON tasks(task_id)
            ''')
            
            conn.commit()
            conn.close()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Obtiene conexión a la base de datos"""
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        return conn
    
    async def enqueue(self, task: Task) -> bool:
        """Agrega tarea a la cola"""
        try:
            with self._lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO tasks 
                    (task_id, task_type, payload, priority, status, created_at, 
                     started_at, completed_at, worker_id, retry_count, 
                     max_retries, error_message, result, timeout)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    task.task_id,
                    task.task_type,
                    json.dumps(task.payload),
                    task.priority.value,
                    task.status.value,
                    task.created_at,
                    task.started_at,
                    task.completed_at,
                    task.worker_id,
                    task.retry_count,
                    task.max_retries,
                    task.error_message,
                    json.dumps(task.result) if task.result else None,
                    task.timeout
                ))
                
                conn.commit()
                conn.close()
            
            logger.debug("task_queue.enqueued", task_id=task.task_id, priority=task.priority.name)
            return True
            
        except Exception as e:
            logger.error("task_queue.enqueue_failed", task_id=task.task_id, error=str(e))
            return False
    
    async def dequeue(self, priorities: Optional[List[TaskPriority]] = None) -> Optional[Task]:
        """Obtiene siguiente tarea disponible (por prioridad)"""
        try:
            with self._lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                # Estados válidos para dequeuar
                valid_statuses = ['pending', 'retrying']
                
                if priorities:
                    priority_values = [p.value for p in priorities]
                    placeholders = ','.join('?' * len(valid_statuses))
                    priority_placeholders = ','.join('?' * len(priorities))
                    
                    query = f'''
                        SELECT * FROM tasks 
                        WHERE status IN ({placeholders})
                        AND priority IN ({priority_placeholders})
                        ORDER BY priority ASC, created_at ASC
                        LIMIT 1
                    '''
                    params = valid_statuses + priority_values
                else:
                    placeholders = ','.join('?' * len(valid_statuses))
                    
                    query = f'''
                        SELECT * FROM tasks 
                        WHERE status IN ({placeholders})
                        ORDER BY priority ASC, created_at ASC
                        LIMIT 1
                    '''
                    params = valid_statuses
                
                cursor.execute(query, params)
                row = cursor.fetchone()
                
                if row:
                    task_data = dict(row)
                    task_data['payload'] = json.loads(task_data['payload'])
                    if task_data['result']:
                        task_data['result'] = json.loads(task_data['result'])
                    
                    # Actualizar estado a 'running' inmediatamente en los datos
                    task_data['status'] = 'running'
                    task_data['started_at'] = time.time()
                    
                    task = Task.from_dict(task_data)
                    
                    # Actualizar en DB
                    cursor.execute('''
                        UPDATE tasks SET status = ?, started_at = ? WHERE task_id = ?
                    ''', ('running', task_data['started_at'], task.task_id))
                    
                    conn.commit()
                    conn.close()
                    
                    logger.debug("task_queue.dequeued", task_id=task.task_id)
                    return task
                
                conn.close()
                return None
                
        except Exception as e:
            logger.error("task_queue.dequeue_failed", error=str(e))
            return None
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        """Obtiene tarea por ID"""
        try:
            with self._lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute('SELECT * FROM tasks WHERE task_id = ?', (task_id,))
                row = cursor.fetchone()
                conn.close()
                
                if row:
                    task_data = dict(row)
                    task_data['payload'] = json.loads(task_data['payload'])
                    if task_data['result']:
                        task_data['result'] = json.loads(task_data['result'])
                    return Task.from_dict(task_data)
                
                return None
                
        except Exception as e:
            logger.error("task_queue.get_task_failed", task_id=task_id, error=str(e))
            return None
    
    async def update_task(self, task: Task) -> bool:
        """Actualiza tarea existente"""
        return await self.enqueue(task)
    
    async def remove_task(self, task_id: str) -> bool:
        """Elimina tarea de la cola"""
        try:
            with self._lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute('DELETE FROM tasks WHERE task_id = ?', (task_id,))
                deleted = cursor.rowcount > 0
                
                conn.commit()
                conn.close()
                
                if deleted:
                    logger.debug("task_queue.removed", task_id=task_id)
                else:
                    logger.warning("task_queue.not_found", task_id=task_id)
                
                return deleted
                
        except Exception as e:
            logger.error("task_queue.remove_failed", task_id=task_id, error=str(e))
            return False
    
    async def get_queue_size(self) -> int:
        """Obtiene tamaño de la cola"""
        try:
            with self._lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT COUNT(*) FROM tasks 
                    WHERE status IN ('pending', 'queued', 'retrying')
                ''')
                count = cursor.fetchone()[0]
                conn.close()
                
                return count
                
        except Exception as e:
            logger.error("task_queue.count_failed", error=str(e))
            return 0
    
    async def clear(self) -> bool:
        """Limpia todas las tareas"""
        try:
            with self._lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute('DELETE FROM tasks')
                conn.commit()
                conn.close()
                
                logger.info("task_queue.cleared")
                return True
                
        except Exception as e:
            logger.error("task_queue.clear_failed", error=str(e))
            return False
    
    async def get_pending_tasks(self, limit: int = 100) -> List[Task]:
        """Obtiene lista de tareas pendientes"""
        try:
            with self._lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM tasks 
                    WHERE status IN ('pending', 'queued', 'retrying')
                    ORDER BY priority ASC, created_at ASC
                    LIMIT ?
                ''', (limit,))
                
                rows = cursor.fetchall()
                conn.close()
                
                tasks = []
                for row in rows:
                    task_data = dict(row)
                    task_data['payload'] = json.loads(task_data['payload'])
                    if task_data['result']:
                        task_data['result'] = json.loads(task_data['result'])
                    tasks.append(Task.from_dict(task_data))
                
                return tasks
                
        except Exception as e:
            logger.error("task_queue.get_pending_failed", error=str(e))
            return []
    
    async def get_stale_tasks(self, max_age_seconds: float = 3600) -> List[Task]:
        """Obtiene tareas antiguas que pueden necesitar cleanup"""
        try:
            with self._lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cutoff_time = time.time() - max_age_seconds
                
                cursor.execute('''
                    SELECT * FROM tasks 
                    WHERE status IN ('running', 'queued')
                    AND created_at < ?
                ''', (cutoff_time,))
                
                rows = cursor.fetchall()
                conn.close()
                
                tasks = []
                for row in rows:
                    task_data = dict(row)
                    task_data['payload'] = json.loads(task_data['payload'])
                    if task_data['result']:
                        task_data['result'] = json.loads(task_data['result'])
                    tasks.append(Task.from_dict(task_data))
                
                return tasks
                
        except Exception as e:
            logger.error("task_queue.get_stale_failed", error=str(e))
            return []


class BackpressureController:
    """Controla backpressure para evitar sobrecarga del sistema"""
    
    def __init__(self, 
                 max_queue_size: int = 1000,
                 warning_threshold: float = 0.8,
                 critical_threshold: float = 0.95):
        self.max_queue_size = max_queue_size
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self.current_size = 0
        self.is_accepting = True
        self.last_warning_time = 0
        
    async def update_size(self, size: int):
        """Actualiza tamaño actual de la cola"""
        self.current_size = size
        utilization = size / self.max_queue_size if self.max_queue_size > 0 else 0
        
        if utilization >= self.critical_threshold:
            if not self.is_accepting:
                return  # Ya está en estado crítico
            
            self.is_accepting = False
            logger.critical("backpressure.critical", 
                          queue_size=size, 
                          max_size=self.max_queue_size,
                          utilization=utilization * 100)
        
        elif utilization >= self.warning_threshold:
            current_time = time.time()
            if current_time - self.last_warning_time > 60:  # Warning cada 60s máx
                self.last_warning_time = current_time
                logger.warning("backpressure.warning", 
                             queue_size=size, 
                             max_size=self.max_queue_size,
                             utilization=utilization * 100)
            self.is_accepting = True
        
        else:
            self.is_accepting = True
    
    def can_accept(self) -> bool:
        """Verifica si se puede aceptar nuevas tareas"""
        return self.is_accepting
    
    def get_utilization(self) -> float:
        """Obtiene porcentaje de utilización"""
        return (self.current_size / self.max_queue_size * 100) if self.max_queue_size > 0 else 0


class TaskQueueService:
    """Servicio principal de cola de tareas"""
    
    def __init__(self, backend: Optional[TaskQueueBackend] = None):
        self.backend = backend or SQLiteTaskQueue()
        self.backpressure = BackpressureController(max_queue_size=1000)
        self.processors: Dict[str, Callable] = {}
        self.is_running = False
        self.worker_tasks: List[asyncio.Task] = []
        self.num_workers = 4
        self.max_concurrent_per_worker = 5
        self.semaphore: Optional[asyncio.Semaphore] = None
        
    async def start(self, num_workers: int = 4):
        """Inicia el servicio de procesamiento de cola"""
        self.num_workers = num_workers
        self.semaphore = asyncio.Semaphore(num_workers * self.max_concurrent_per_worker)
        self.is_running = True
        
        # Iniciar workers
        for i in range(num_workers):
            worker_task = asyncio.create_task(self._worker_loop(f"worker-{i}"))
            self.worker_tasks.append(worker_task)
        
        # Iniciar monitoreo de backpressure
        asyncio.create_task(self._backpressure_monitor())
        
        logger.info("task_queue.started", num_workers=num_workers)
    
    async def stop(self):
        """Detiene el servicio"""
        self.is_running = False
        
        # Cancelar todos los workers
        for task in self.worker_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        self.worker_tasks = []
        logger.info("task_queue.stopped")
    
    def register_processor(self, task_type: str, handler: Callable):
        """Registra procesador para tipo de tarea"""
        self.processors[task_type] = handler
        logger.info("task_queue.processor_registered", task_type=task_type)
    
    async def submit_task(self, 
                         task_type: str,
                         payload: Dict[str, Any],
                         priority: TaskPriority = TaskPriority.NORMAL,
                         task_id: Optional[str] = None,
                         timeout: Optional[float] = None,
                         max_retries: int = 3) -> Optional[str]:
        """Envía tarea a la cola"""
        
        # Verificar backpressure
        if not self.backpressure.can_accept():
            logger.error("task_queue.backpressure_rejected", task_type=task_type)
            return None
        
        # Generar ID si no se proporciona
        if task_id is None:
            task_id = f"{task_type}_{int(time.time() * 1000)}_{id(payload)}"
        
        # Crear tarea
        task = Task(
            task_id=task_id,
            task_type=task_type,
            payload=payload,
            priority=priority,
            timeout=timeout,
            max_retries=max_retries
        )
        
        # Encolar
        success = await self.backend.enqueue(task)
        
        if success:
            # Actualizar backpressure
            queue_size = await self.backend.get_queue_size()
            await self.backpressure.update_size(queue_size)
            
            logger.info("task_queue.submitted", 
                       task_id=task_id, 
                       task_type=task_type,
                       priority=priority.name)
            return task_id
        
        return None
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene estado de una tarea"""
        task = await self.backend.get_task(task_id)
        
        if task:
            return {
                'task_id': task.task_id,
                'status': task.status.value,
                'progress': self._calculate_progress(task),
                'created_at': task.created_at,
                'started_at': task.started_at,
                'completed_at': task.completed_at,
                'worker_id': task.worker_id,
                'retry_count': task.retry_count,
                'error_message': task.error_message,
                'has_result': task.result is not None
            }
        
        return None
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancela una tarea pendiente"""
        task = await self.backend.get_task(task_id)
        
        if not task:
            return False
        
        if task.status in [TaskStatus.RUNNING, TaskStatus.COMPLETED]:
            logger.warning("task_queue.cannot_cancel", 
                          task_id=task_id, 
                          status=task.status.value)
            return False
        
        task.status = TaskStatus.CANCELLED
        task.completed_at = time.time()
        
        return await self.backend.update_task(task)
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de la cola"""
        queue_size = await self.backend.get_queue_size()
        pending_tasks = await self.backend.get_pending_tasks(limit=1000)
        
        # Contar por prioridad
        priority_counts = {p.name: 0 for p in TaskPriority}
        for task in pending_tasks:
            priority_counts[task.priority.name] += 1
        
        # Contar por tipo
        type_counts: Dict[str, int] = {}
        for task in pending_tasks:
            type_counts[task.task_type] = type_counts.get(task.task_type, 0) + 1
        
        return {
            'queue_size': queue_size,
            'max_size': self.backpressure.max_queue_size,
            'utilization_percent': self.backpressure.get_utilization(),
            'is_accepting': self.backpressure.can_accept(),
            'by_priority': priority_counts,
            'by_type': type_counts,
            'num_workers': self.num_workers,
            'active_workers': len([t for t in self.worker_tasks if not t.done()])
        }
    
    def _calculate_progress(self, task: Task) -> float:
        """Calcula progreso estimado de la tarea"""
        if task.status == TaskStatus.COMPLETED:
            return 100.0
        elif task.status == TaskStatus.FAILED or task.status == TaskStatus.CANCELLED:
            return 0.0
        elif task.status == TaskStatus.RUNNING:
            # Estimación básica basada en tiempo
            if task.started_at:
                elapsed = time.time() - task.started_at
                if task.timeout:
                    return min(100.0, (elapsed / task.timeout) * 100)
                return 50.0  # Default 50% si no hay timeout
            return 0.0
        else:
            return 0.0
    
    async def _worker_loop(self, worker_id: str):
        """Bucle principal de un worker"""
        logger.info("task_queue.worker_started", worker_id=worker_id)
        
        while self.is_running:
            try:
                async with self.semaphore:
                    # Obtener siguiente tarea
                    task = await self.backend.dequeue()
                    
                    if not task:
                        await asyncio.sleep(0.5)  # Esperar si no hay tareas
                        continue
                    
                    # Verificar si expiró
                    if task.is_expired():
                        logger.warning("task_queue.task_expired", task_id=task.task_id)
                        task.status = TaskStatus.FAILED
                        task.error_message = "Task expired"
                        task.completed_at = time.time()
                        await self.backend.update_task(task)
                        continue
                    
                    # Procesar tarea
                    await self._process_task(task, worker_id)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("task_queue.worker_error", 
                           worker_id=worker_id, 
                           error=str(e))
                await asyncio.sleep(1)
        
        logger.info("task_queue.worker_stopped", worker_id=worker_id)
    
    async def _process_task(self, task: Task, worker_id: str):
        """Procesa una tarea individual"""
        logger.info("task_queue.processing", 
                   task_id=task.task_id, 
                   task_type=task.task_type,
                   worker_id=worker_id)
        
        # Actualizar estado a running
        task.status = TaskStatus.RUNNING
        task.started_at = time.time()
        task.worker_id = worker_id
        await self.backend.update_task(task)
        
        # Buscar procesador
        processor = self.processors.get(task.task_type)
        
        if not processor:
            error_msg = f"No processor registered for task type: {task.task_type}"
            logger.error("task_queue.no_processor", task_id=task.task_id, error=error_msg)
            await self._handle_failure(task, error_msg)
            return
        
        try:
            # Ejecutar procesador
            if asyncio.iscoroutinefunction(processor):
                result = await processor(task.payload)
            else:
                result = processor(task.payload)
            
            # Éxito
            task.status = TaskStatus.COMPLETED
            task.completed_at = time.time()
            task.result = result
            await self.backend.update_task(task)
            
            logger.info("task_queue.completed", 
                       task_id=task.task_id, 
                       duration=time.time() - task.started_at)
            
        except Exception as e:
            error_msg = str(e)
            logger.error("task_queue.failed", 
                        task_id=task.task_id, 
                        error=error_msg)
            await self._handle_failure(task, error_msg)
    
    async def _handle_failure(self, task: Task, error_msg: str):
        """Maneja fallo de tarea con reintentos"""
        task.error_message = error_msg
        task.retry_count += 1
        
        if task.retry_count < task.max_retries:
            # Reintentar
            task.status = TaskStatus.RETRYING
            await self.backend.update_task(task)
            
            # Backoff exponencial
            delay = min(300, 2 ** task.retry_count)  # Máx 5 minutos
            logger.info("task_queue.retry_scheduled", 
                       task_id=task.task_id, 
                       retry_count=task.retry_count,
                       delay=delay)
            
            await asyncio.sleep(delay)
            
            # Volver a poner en pending
            task.status = TaskStatus.PENDING
            task.started_at = None
            task.worker_id = None
            await self.backend.update_task(task)
        
        else:
            # Fallo definitivo
            task.status = TaskStatus.FAILED
            task.completed_at = time.time()
            await self.backend.update_task(task)
            
            logger.error("task_queue.max_retries_exceeded", 
                        task_id=task.task_id, 
                        total_retries=task.retry_count)
    
    async def _backpressure_monitor(self):
        """Monitorea backpressure continuamente"""
        while self.is_running:
            try:
                queue_size = await self.backend.get_queue_size()
                await self.backpressure.update_size(queue_size)
                await asyncio.sleep(5)  # Chequear cada 5 segundos
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("task_queue.backpressure_monitor_error", error=str(e))
                await asyncio.sleep(10)


# Singleton instance
_task_queue_service: Optional[TaskQueueService] = None


def get_task_queue_service() -> TaskQueueService:
    """Obtiene instancia singleton del servicio"""
    global _task_queue_service
    if _task_queue_service is None:
        _task_queue_service = TaskQueueService()
    return _task_queue_service


async def create_task_queue_service(db_path: str = "synapse_tasks.db") -> TaskQueueService:
    """Crea y configura servicio de cola de tareas"""
    global _task_queue_service
    
    backend = SQLiteTaskQueue(db_path=db_path)
    _task_queue_service = TaskQueueService(backend=backend)
    
    return _task_queue_service

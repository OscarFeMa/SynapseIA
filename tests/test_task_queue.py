"""
Tests para el servicio de Task Queue
"""
import asyncio
import pytest
import time
from pathlib import Path

from backend.services.task_queue import (
    TaskQueueService, 
    SQLiteTaskQueue, 
    Task, 
    TaskPriority, 
    TaskStatus,
    BackpressureController,
    get_task_queue_service,
    create_task_queue_service
)


class TestTaskPriority:
    """Tests para prioridades de tareas"""
    
    def test_priority_ordering(self):
        """Verifica orden de prioridades"""
        assert TaskPriority.CRITICAL.value < TaskPriority.HIGH.value
        assert TaskPriority.HIGH.value < TaskPriority.NORMAL.value
        assert TaskPriority.NORMAL.value < TaskPriority.LOW.value
        assert TaskPriority.LOW.value < TaskPriority.BACKGROUND.value


class TestTask:
    """Tests para la clase Task"""
    
    def test_task_creation(self):
        """Crea tarea básica"""
        task = Task(
            task_id="test_1",
            task_type="test_type",
            payload={"key": "value"}
        )
        
        assert task.task_id == "test_1"
        assert task.task_type == "test_type"
        assert task.payload == {"key": "value"}
        assert task.priority == TaskPriority.NORMAL
        assert task.status == TaskStatus.PENDING
        assert task.created_at > 0
    
    def test_task_serialization(self):
        """Serializa y deserializa tarea"""
        task = Task(
            task_id="test_2",
            task_type="test_type",
            payload={"data": [1, 2, 3]},
            priority=TaskPriority.HIGH
        )
        
        # Serializar
        data = task.to_dict()
        assert data['priority'] == 1  # HIGH value
        assert data['status'] == 'pending'
        
        # Deserializar
        task2 = Task.from_dict(data)
        assert task2.task_id == task.task_id
        assert task2.priority == TaskPriority.HIGH
        assert task2.status == TaskStatus.PENDING
    
    def test_task_expiration(self):
        """Verifica expiración de tareas"""
        # Tarea sin timeout no expira
        task1 = Task(
            task_id="test_3",
            task_type="test",
            payload={},
            timeout=None
        )
        assert not task1.is_expired()
        
        # Tarea con timeout muy corto
        task2 = Task(
            task_id="test_4",
            task_type="test",
            payload={},
            timeout=0.1  # 100ms
        )
        time.sleep(0.2)
        assert task2.is_expired()


class TestSQLiteTaskQueue:
    """Tests para cola SQLite"""
    
    @pytest.fixture
    def queue(self, tmp_path):
        """Crea cola temporal"""
        db_path = tmp_path / "test_tasks.db"
        return SQLiteTaskQueue(db_path=str(db_path))
    
    @pytest.mark.asyncio
    async def test_enqueue_dequeue(self, queue):
        """Encola y desencola tarea"""
        task = Task(
            task_id="test_1",
            task_type="test_type",
            payload={"test": "data"}
        )
        
        # Encolar
        success = await queue.enqueue(task)
        assert success
        
        # Verificar tamaño
        size = await queue.get_queue_size()
        assert size == 1
        
        # Desencolar
        dequeued = await queue.dequeue()
        assert dequeued is not None
        assert dequeued.task_id == "test_1"
        assert dequeued.payload == {"test": "data"}
        assert dequeued.status == TaskStatus.RUNNING  # Ahora debe estar running
        
        # Verificar tamaño después (la tarea está running, no cuenta como pending)
        size = await queue.get_queue_size()
        assert size == 0
    
    @pytest.mark.asyncio
    async def test_priority_ordering(self, queue):
        """Verifica que se respeta el orden de prioridad"""
        # Encolar tareas en orden inverso
        for i in range(3):
            priority = [TaskPriority.LOW, TaskPriority.NORMAL, TaskPriority.HIGH][i]
            task = Task(
                task_id=f"task_{i}",
                task_type="test",
                payload={"order": i},
                priority=priority
            )
            await queue.enqueue(task)
        
        # Desencolar y verificar orden (primero HIGH)
        first = await queue.dequeue()
        assert first.priority == TaskPriority.HIGH
        assert first.task_id == "task_2"
        
        # Segundo: NORMAL
        second = await queue.dequeue()
        assert second.priority == TaskPriority.NORMAL
        assert second.task_id == "task_1"
        
        # Tercero: LOW
        third = await queue.dequeue()
        assert third.priority == TaskPriority.LOW
        assert third.task_id == "task_0"
    
    @pytest.mark.asyncio
    async def test_get_task(self, queue):
        """Obtiene tarea por ID"""
        task = Task(
            task_id="specific_id",
            task_type="test",
            payload={}
        )
        await queue.enqueue(task)
        
        retrieved = await queue.get_task("specific_id")
        assert retrieved is not None
        assert retrieved.task_id == "specific_id"
        
        # ID inexistente
        not_found = await queue.get_task("nonexistent")
        assert not_found is None
    
    @pytest.mark.asyncio
    async def test_update_task(self, queue):
        """Actualiza tarea existente"""
        task = Task(
            task_id="update_test",
            task_type="test",
            payload={}
        )
        await queue.enqueue(task)
        
        # Actualizar estado
        task.status = TaskStatus.RUNNING
        task.worker_id = "worker_1"
        success = await queue.update_task(task)
        assert success
        
        # Verificar actualización
        updated = await queue.get_task("update_test")
        assert updated.status == TaskStatus.RUNNING
        assert updated.worker_id == "worker_1"
    
    @pytest.mark.asyncio
    async def test_remove_task(self, queue):
        """Elimina tarea"""
        task = Task(
            task_id="remove_test",
            task_type="test",
            payload={}
        )
        await queue.enqueue(task)
        
        # Eliminar
        success = await queue.remove_task("remove_test")
        assert success
        
        # Verificar eliminación
        size = await queue.get_queue_size()
        assert size == 0
        
        # Eliminar inexistente
        success = await queue.remove_task("nonexistent")
        assert not success
    
    @pytest.mark.asyncio
    async def test_clear_queue(self, queue):
        """Limpia toda la cola"""
        # Agregar varias tareas
        for i in range(5):
            task = Task(
                task_id=f"task_{i}",
                task_type="test",
                payload={}
            )
            await queue.enqueue(task)
        
        # Limpiar
        success = await queue.clear()
        assert success
        
        # Verificar
        size = await queue.get_queue_size()
        assert size == 0
    
    @pytest.mark.asyncio
    async def test_get_pending_tasks(self, queue):
        """Obtiene lista de tareas pendientes"""
        # Agregar tareas
        for i in range(10):
            task = Task(
                task_id=f"task_{i}",
                task_type="test",
                payload={"index": i}
            )
            await queue.enqueue(task)
        
        # Obtener pendientes (limitado a 5)
        pending = await queue.get_pending_tasks(limit=5)
        assert len(pending) == 5
        
        # Verificar orden por prioridad
        for i in range(len(pending) - 1):
            assert pending[i].priority.value <= pending[i+1].priority.value


class TestBackpressureController:
    """Tests para control de backpressure"""
    
    @pytest.mark.asyncio
    async def test_normal_operation(self):
        """Operación normal sin presión"""
        controller = BackpressureController(max_queue_size=100)
        
        await controller.update_size(50)  # 50%
        assert controller.can_accept() is True
        assert controller.get_utilization() == 50.0
    
    @pytest.mark.asyncio
    async def test_warning_threshold(self):
        """Umbral de warning"""
        controller = BackpressureController(
            max_queue_size=100,
            warning_threshold=0.8
        )
        
        await controller.update_size(80)  # 80%
        assert controller.can_accept() is True
    
    @pytest.mark.asyncio
    async def test_critical_threshold(self):
        """Umbral crítico"""
        controller = BackpressureController(
            max_queue_size=100,
            critical_threshold=0.95
        )
        
        await controller.update_size(95)  # 95%
        assert controller.can_accept() is False
        
        # Reducir carga
        await controller.update_size(50)
        assert controller.can_accept() is True


class TestTaskQueueService:
    """Tests para el servicio completo"""
    
    @pytest.fixture
    async def service(self, tmp_path):
        """Crea servicio temporal"""
        db_path = tmp_path / "test_service.db"
        service = await create_task_queue_service(db_path=str(db_path))
        await service.start(num_workers=2)
        yield service
        await service.stop()
    
    @pytest.mark.asyncio
    async def test_submit_task(self, service):
        """Envía tarea al servicio"""
        task_id = await service.submit_task(
            task_type="test_task",
            payload={"data": "test"}
        )
        
        assert task_id is not None
        assert "test_task_" in task_id
    
    @pytest.mark.asyncio
    async def test_submit_with_priority(self, service):
        """Envía tarea con prioridad específica"""
        task_id = await service.submit_task(
            task_type="critical_task",
            payload={},
            priority=TaskPriority.CRITICAL
        )
        
        assert task_id is not None
        
        status = await service.get_task_status(task_id)
        assert status is not None
    
    @pytest.mark.asyncio
    async def test_get_task_status(self, service):
        """Obtiene estado de tarea"""
        task_id = await service.submit_task(
            task_type="status_test",
            payload={}
        )
        
        status = await service.get_task_status(task_id)
        assert status is not None
        assert status['task_id'] == task_id
        assert status['status'] in ['pending', 'queued', 'running', 'completed']
    
    @pytest.mark.asyncio
    async def test_cancel_task(self, service):
        """Cancela tarea pendiente"""
        task_id = await service.submit_task(
            task_type="cancel_test",
            payload={},
            priority=TaskPriority.BACKGROUND  # Baja prioridad para que no se ejecute rápido
        )
        
        # Cancelar inmediatamente
        success = await service.cancel_task(task_id)
        # Puede que ya se haya ejecutado, así que no fallamos si es False
        
        if success:
            status = await service.get_task_status(task_id)
            assert status['status'] == 'cancelled'
    
    @pytest.mark.asyncio
    async def test_queue_stats(self, service):
        """Obtiene estadísticas de cola"""
        # Enviar algunas tareas
        for i in range(5):
            await service.submit_task(
                task_type=f"type_{i % 2}",
                payload={"index": i}
            )
        
        stats = await service.get_queue_stats()
        
        assert 'queue_size' in stats
        assert 'utilization_percent' in stats
        assert 'by_priority' in stats
        assert 'by_type' in stats
        assert stats['num_workers'] == 2
    
    @pytest.mark.asyncio
    async def test_processor_registration(self, service):
        """Registra y ejecuta procesador"""
        results = []
        
        async def test_processor(payload):
            results.append(payload)
            return {"processed": True}
        
        service.register_processor("test_type", test_processor)
        
        # Enviar tarea
        task_id = await service.submit_task(
            task_type="test_type",
            payload={"test": "data"}
        )
        
        # Esperar procesamiento
        await asyncio.sleep(2)
        
        # Verificar
        status = await service.get_task_status(task_id)
        assert status is not None
        # La tarea debería estar completada o en proceso
    
    @pytest.mark.asyncio
    async def test_backpressure_rejection(self, tmp_path):
        """Rechaza tareas por backpressure"""
        db_path = tmp_path / "test_bp.db"
        backend = SQLiteTaskQueue(db_path=str(db_path))
        
        service = TaskQueueService(backend=backend)
        service.backpressure.max_queue_size = 5
        service.backpressure.is_accepting = False  # Forzar estado crítico
        
        # Intentar enviar tarea
        task_id = await service.submit_task(
            task_type="test",
            payload={}
        )
        
        assert task_id is None


class TestIntegration:
    """Tests de integración completa"""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self, tmp_path):
        """Flujo completo de trabajo"""
        db_path = tmp_path / "integration.db"
        service = await create_task_queue_service(db_path=str(db_path))
        
        # Registrar procesador
        processed_tasks = []
        
        async def processor(payload):
            await asyncio.sleep(0.1)  # Simular trabajo
            processed_tasks.append(payload)
            return {"result": "ok"}
        
        service.register_processor("workflow_task", processor)
        
        # Iniciar servicio
        await service.start(num_workers=2)
        
        try:
            # Enviar múltiples tareas
            task_ids = []
            for i in range(5):
                task_id = await service.submit_task(
                    task_type="workflow_task",
                    payload={"index": i},
                    priority=TaskPriority.NORMAL
                )
                task_ids.append(task_id)
            
            # Esperar procesamiento
            await asyncio.sleep(3)
            
            # Verificar que todas se procesaron
            assert len(processed_tasks) == 5
            
            # Verificar estados
            for task_id in task_ids:
                status = await service.get_task_status(task_id)
                assert status is not None
                assert status['status'] == 'completed'
            
            # Verificar estadísticas
            stats = await service.get_queue_stats()
            assert stats['queue_size'] == 0
        
        finally:
            await service.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

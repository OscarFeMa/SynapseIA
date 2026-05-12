"""
Synapse Council v2.0 - Backend Tests
Test suite con pytest y cobertura 80%
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch
import json
from datetime import datetime

from backend.config import get_settings
from backend.database.local_db import init_db, get_session
from backend.services.supabase_sync import SupabaseSyncService
from backend.services.cache_service import CacheService
from backend.services.worker_pool import WorkerPool, LoadBalancingStrategy
from backend.monitoring.metrics import MetricsCollector
from backend.engine.sequential_debate_controller import SequentialDebateController


class TestConfig:
    """Configuración de tests"""
    
    @pytest.fixture
    def settings(self):
        """Settings de prueba"""
        return get_settings()
    
    @pytest.fixture
    async def db_session(self):
        """Sesión de BD para tests"""
        await init_db()
        async for session in get_session():
            yield session
            await session.rollback()


class TestSupabaseSync:
    """Tests para Supabase Sync Service"""
    
    @pytest.fixture
    def supabase_service(self):
        """Instancia de SupabaseSyncService para tests"""
        return SupabaseSyncService()
    
    @pytest.mark.asyncio
    async def test_connection_disabled(self, supabase_service):
        """Test conexión cuando Supabase está deshabilitado"""
        with patch.object(supabase_service, 'enabled', False):
            result = await supabase_service.test_connection()
            
        assert result['status'] == 'disabled'
        assert 'Supabase not configured' in result['message']
    
    @pytest.mark.asyncio
    async def test_sync_debate_disabled(self, supabase_service):
        """Test sincronización cuando está deshabilitado"""
        debate_data = {
            'id': 'test-debate-1',
            'topic': 'Test Debate',
            'status': 'completed'
        }
        
        with patch.object(supabase_service, 'enabled', False):
            result = await supabase_service.sync_debate(debate_data)
            
        assert result['synced'] is False
        assert 'Supabase not enabled' in result['reason']
    
    @pytest.mark.asyncio
    async def test_sync_debate_success(self, supabase_service):
        """Test sincronización exitosa"""
        debate_data = {
            'id': 'test-debate-2',
            'topic': 'Test Debate Success',
            'mode': 'standard',
            'status': 'completed',
            'total_turns': 4,
            'total_tokens_in': 1000,
            'total_tokens_out': 2000,
            'total_latency_ms': 5000,
            'final_verdict': 'Test verdict',
            'turns': [
                {
                    'turn_number': 1,
                    'agent_id': 'analyst_1',
                    'agent_name': 'Test Analyst',
                    'agent_role': 'analyst',
                    'model': 'test-model',
                    'provider': 'test-provider',
                    'node': 'LOCAL',
                    'engine': 'ollama',
                    'prompt_sent': 'Test prompt',
                    'response_received': 'Test response',
                    'tokens_in': 100,
                    'tokens_out': 200,
                    'latency_ms': 1000,
                    'status': 'completed'
                }
            ]
        }
        
        # Mock cliente HTTP
        mock_client = AsyncMock()
        mock_client.post.return_value = AsyncMock(status_code=200)
        supabase_service.client = mock_client
        
        with patch.object(supabase_service, 'enabled', True):
            result = await supabase_service.sync_debate(debate_data)
            
        assert result['synced'] is True
        assert result['debate_id'] == 'test-debate-2'
        assert result['turns_synced'] == 1
        
        # Verificar que se llamó al cliente
        assert mock_client.post.call_count >= 2  # Debate + Turn


class TestCacheService:
    """Tests para Cache Service"""
    
    @pytest.fixture
    def cache_service(self):
        """Instancia de CacheService para tests"""
        return CacheService()
    
    @pytest.mark.asyncio
    async def test_cache_disabled(self, cache_service):
        """Test cuando caché está deshabilitado"""
        with patch.object(cache_service, 'enabled', False):
            result = await cache_service.get('test_key')
            assert result is None
            
            success = await cache_service.set('test_key', 'test_value')
            assert success is False
    
    @pytest.mark.asyncio
    async def test_cache_set_get(self, cache_service):
        """Test básico set/get"""
        with patch.object(cache_service, 'enabled', True):
            # Mock cliente Redis
            mock_client = AsyncMock()
            mock_client.ping.return_value = True
            mock_client.get.return_value = json.dumps('test_value')
            mock_client.setex.return_value = True
            cache_service.client = mock_client
            
            # Test set
            success = await cache_service.set('test_key', 'test_value', ttl=60)
            assert success is True
            
            # Test get
            result = await cache_service.get('test_key')
            assert result == 'test_value'
    
    @pytest.mark.asyncio
    async def test_agent_response_cache(self, cache_service):
        """Test caché de respuestas de agente"""
        with patch.object(cache_service, 'enabled', True):
            mock_client = AsyncMock()
            mock_client.ping.return_value = True
            mock_client.get.return_value = None
            mock_client.setex.return_value = True
            cache_service.client = mock_client
            
            # Test cache miss
            result = await cache_service.get_agent_response(
                'test prompt', 'analyst', 'test-model'
            )
            assert result is None
            
            # Test cache set
            success = await cache_service.set_agent_response(
                'test prompt', 'analyst', 'test-model', 'test response'
            )
            assert success is True
            
            # Test cache hit
            mock_client.get.return_value = json.dumps('test response')
            result = await cache_service.get_agent_response(
                'test prompt', 'analyst', 'test-model'
            )
            assert result == 'test response'


class TestWorkerPool:
    """Tests para Worker Pool"""
    
    @pytest.fixture
    def worker_pool(self):
        """Instancia de WorkerPool para tests"""
        return WorkerPool(LoadBalancingStrategy.ROUND_ROBIN)
    
    @pytest.mark.asyncio
    async def test_add_worker(self, worker_pool):
        """Test agregar worker al pool"""
        success = await worker_pool.add_worker(
            'worker-1', 'localhost', 8001, max_concurrent=3
        )
        
        assert success is True
        assert 'worker-1' in worker_pool.workers
        
        worker = worker_pool.workers['worker-1']
        assert worker.host == 'localhost'
        assert worker.port == 8001
        assert worker.max_concurrent == 3
    
    @pytest.mark.asyncio
    async def test_add_duplicate_worker(self, worker_pool):
        """Test agregar worker duplicado"""
        await worker_pool.add_worker('worker-1', 'localhost', 8001)
        
        success = await worker_pool.add_worker('worker-1', 'localhost', 8002)
        assert success is False
    
    @pytest.mark.asyncio
    async def test_select_worker_round_robin(self, worker_pool):
        """Test selección Round Robin"""
        await worker_pool.add_worker('worker-1', 'localhost', 8001)
        await worker_pool.add_worker('worker-2', 'localhost', 8002)
        
        # Primera selección
        worker1 = await worker_pool.select_worker()
        assert worker1.worker_id == 'worker-1'
        
        # Segunda selección
        worker2 = await worker_pool.select_worker()
        assert worker2.worker_id == 'worker-2'
        
        # Tercera selección (vuelve al inicio)
        worker3 = await worker_pool.select_worker()
        assert worker3.worker_id == 'worker-1'
    
    @pytest.mark.asyncio
    async def test_acquire_release_worker(self, worker_pool):
        """Test adquirir y liberar worker"""
        await worker_pool.add_worker('worker-1', 'localhost', 8001, max_concurrent=1)
        
        worker = worker_pool.workers['worker-1']
        
        # Test acquire
        acquired = await worker.acquire()
        assert acquired is True
        assert worker.current_load == 1
        
        # Test acquire cuando está lleno
        acquired_full = await worker.acquire()
        assert acquired_full is False
        
        # Test release
        await worker.release(success=True, response_time=1.5)
        assert worker.current_load == 0
        assert worker.successful_requests == 1
        assert worker.get_avg_response_time() == 1.5


class TestMetricsCollector:
    """Tests para Metrics Collector"""
    
    @pytest.fixture
    def metrics_collector(self):
        """Instancia de MetricsCollector para tests"""
        return MetricsCollector()
    
    @pytest.mark.asyncio
    async def test_record_debate_complete(self, metrics_collector):
        """Test registrar debate completado"""
        metrics_collector.record_debate_start('standard', 'test-debate-1')
        metrics_collector.record_debate_complete('standard', 120.5, 'test-debate-1')
        
        summary = metrics_collector.get_metrics_summary()
        assert summary['debates_total'] == 1
        assert summary['active_debates'] == 0  # Se decrementó al completar
    
    @pytest.mark.asyncio
    async def test_record_agent_call(self, metrics_collector):
        """Test registrar llamada a agente"""
        metrics_collector.record_agent_call(
            agent_role='analyst',
            provider='ollama',
            node='LOCAL',
            status='success',
            latency=2.5,
            tokens=150,
            model='test-model'
        )
        
        summary = metrics_collector.get_metrics_summary()
        assert summary['debates_total'] == 1  # Se incrementó
    
    def test_categorize_duration(self, metrics_collector):
        """Test categorización de duración"""
        assert metrics_collector._categorize_duration(15) == 'fast'
        assert metrics_collector._categorize_duration(60) == 'normal'
        assert metrics_collector._categorize_duration(200) == 'slow'
        assert metrics_collector._categorize_duration(400) == 'very_slow'


class TestSequentialDebateController:
    """Tests para Sequential Debate Controller"""
    
    @pytest.fixture
    def debate_controller(self):
        """Instancia de SequentialDebateController para tests"""
        return SequentialDebateController()
    
    @pytest.mark.asyncio
    async def test_create_debate_session(self, debate_controller):
        """Test crear sesión de debate"""
        session_id = await debate_controller.create_debate_session(
            topic='Test Debate Topic',
            mode='local_only',
            max_rounds=3
        )
        
        assert session_id is not None
        assert session_id in debate_controller.active_sessions
        
        session = debate_controller.active_sessions[session_id]
        assert session.topic == 'Test Debate Topic'
        assert session.mode == 'local_only'
        assert session.max_rounds == 3
        assert session.status == 'created'
    
    @pytest.mark.asyncio
    async def test_execute_debate_round(self, debate_controller):
        """Test ejecutar ronda de debate"""
        # Crear sesión primero
        session_id = await debate_controller.create_debate_session(
            topic='Test Debate Round',
            mode='local_only',
            max_rounds=1
        )
        
        # Mock de agentes
        with patch.object(debate_controller, '_run_local_agent') as mock_run_agent:
            mock_run_agent.return_value = AsyncMock(
                status='completed',
                response='Test response',
                tokens_used=100,
                latency=2.0
            )
            
            # Ejecutar ronda
            result = await debate_controller.execute_debate_round(
                session_id=session_id,
                round_number=1,
                query='Test query'
            )
            
            assert result is not None
            assert result['round_number'] == 1
            assert result['status'] == 'completed'


class TestIntegration:
    """Tests de integración entre componentes"""
    
    @pytest.mark.asyncio
    async def test_supabase_cache_integration(self):
        """Test integración Supabase + Cache"""
        supabase_service = SupabaseSyncService()
        cache_service = CacheService()
        
        # Mockear ambos servicios
        with patch.object(supabase_service, 'enabled', True), \
             patch.object(cache_service, 'enabled', True):
            
            mock_supabase_client = AsyncMock()
            mock_supabase_client.post.return_value = AsyncMock(status_code=200)
            supabase_service.client = mock_supabase_client
            
            mock_redis_client = AsyncMock()
            mock_redis_client.ping.return_value = True
            mock_redis_client.get.return_value = None
            mock_redis_client.setex.return_value = True
            cache_service.client = mock_redis_client
            
            # Test flujo completo
            debate_data = {
                'id': 'integration-test',
                'topic': 'Integration Test',
                'status': 'completed'
            }
            
            # Sincronizar con Supabase
            sync_result = await supabase_service.sync_debate(debate_data)
            assert sync_result['synced'] is True
            
            # Cachear resumen
            cache_success = await cache_service.set_debate_summary(
                'integration-test', 
                {'status': 'synced', 'timestamp': datetime.now().isoformat()}
            )
            assert cache_success is True
            
            # Recuperar desde caché
            cached = await cache_service.get_debate_summary('integration-test')
            assert cached is not None
            assert cached['status'] == 'synced'


# Tests de configuración
class TestConfig:
    """Tests para configuración"""
    
    def test_settings_instance(self):
        """Test que settings se puede instanciar"""
        settings = get_settings()
        assert settings is not None
        assert hasattr(settings, 'NODE_ROLE')
        assert hasattr(settings, 'DATABASE_URL')
        assert hasattr(settings, 'SUPABASE_URL')
        assert hasattr(settings, 'REDIS_URL')
    
    def test_default_values(self):
        """Test valores por defecto"""
        settings = get_settings()
        assert settings.NODE_ROLE == 'MASTER'
        assert 'sqlite' in settings.DATABASE_URL
        assert settings.REDIS_URL == 'redis://localhost:6379'
        assert settings.METRICS_ENABLED is True


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=backend', '--cov-report=html', '--cov-report=term'])

"""
Synapse Council v2.0 - Redis Cache Service
Servicio de caché para respuestas y datos frecuentes
"""
import json
import hashlib
from typing import Any, Optional, Dict, List
import redis.asyncio as redis
import structlog

from backend.config import get_settings

logger = structlog.get_logger()
settings = get_settings()


class CacheService:
    """Servicio de caché Redis con políticas inteligentes"""
    
    def __init__(self):
        self.redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379')
        self.enabled = bool(self.redis_url)
        self.client: Optional[redis.Redis] = None
        
    async def _get_client(self) -> redis.Redis:
        """Obtiene cliente Redis persistente"""
        if self.client is None:
            try:
                self.client = redis.from_url(
                    self.redis_url,
                    encoding='utf-8',
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    health_check_interval=30
                )
                # Test connection
                await self.client.ping()
                logger.info("cache.redis_connected", url=self.redis_url)
            except Exception as e:
                logger.warning("cache.redis_connection_failed", error=str(e))
                self.enabled = False
                self.client = None
        return self.client
    
    async def get(self, key: str) -> Optional[Any]:
        """Obtiene valor del caché"""
        if not self.enabled:
            return None
            
        try:
            client = await self._get_client()
            if client is None:
                return None
                
            value = await client.get(key)
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return None
        except Exception as e:
            logger.debug("cache.get_failed", key=key, error=str(e))
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Establece valor en caché"""
        if not self.enabled:
            return False
            
        try:
            client = await self._get_client()
            if client is None:
                return False
                
            # Serializar si es objeto
            if not isinstance(value, (str, int, float)):
                value = json.dumps(value, ensure_ascii=False)
                
            result = await client.setex(key, ttl, value)
            if result:
                logger.debug("cache.set_success", key=key, ttl=ttl)
            return bool(result)
        except Exception as e:
            logger.debug("cache.set_failed", key=key, error=str(e))
            return False
    
    async def delete(self, key: str) -> bool:
        """Elimina clave del caché"""
        if not self.enabled:
            return False
            
        try:
            client = await self._get_client()
            if client is None:
                return False
                
            result = await client.delete(key)
            return bool(result)
        except Exception as e:
            logger.debug("cache.delete_failed", key=key, error=str(e))
            return False
    
    async def exists(self, key: str) -> bool:
        """Verifica si clave existe"""
        if not self.enabled:
            return False
            
        try:
            client = await self._get_client()
            if client is None:
                return False
                
            result = await client.exists(key)
            return bool(result)
        except Exception as e:
            logger.debug("cache.exists_failed", key=key, error=str(e))
            return False
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Incrementa contador"""
        if not self.enabled:
            return None
            
        try:
            client = await self._get_client()
            if client is None:
                return None
                
            result = await client.incrby(key, amount)
            return result
        except Exception as e:
            logger.debug("cache.increment_failed", key=key, error=str(e))
            return None
    
    async def get_keys_pattern(self, pattern: str) -> List[str]:
        """Obtiene claves que coinciden con patrón"""
        if not self.enabled:
            return []
            
        try:
            client = await self._get_client()
            if client is None:
                return []
                
            keys = await client.keys(pattern)
            return keys
        except Exception as e:
            logger.debug("cache.keys_failed", pattern=pattern, error=str(e))
            return []
    
    async def clear_pattern(self, pattern: str) -> int:
        """Elimina claves que coinciden con patrón"""
        if not self.enabled:
            return 0
            
        try:
            client = await self._get_client()
            if client is None:
                return 0
                
            keys = await client.keys(pattern)
            if keys:
                result = await client.delete(*keys)
                logger.info("cache.pattern_cleared", pattern=pattern, count=result)
                return result
            return 0
        except Exception as e:
            logger.debug("cache.clear_pattern_failed", pattern=pattern, error=str(e))
            return 0
    
    def _generate_cache_key(self, prefix: str, **kwargs) -> str:
        """Genera clave de caché única"""
        key_data = f"{prefix}:{json.dumps(kwargs, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    # Métodos específicos para Synapse
    async def get_agent_response(self, prompt: str, agent_role: str, model: str) -> Optional[str]:
        """Obtiene respuesta cacheada de agente"""
        cache_key = self._generate_cache_key(
            'agent_response',
            prompt=prompt[:1000],  # Limitar tamaño
            agent_role=agent_role,
            model=model
        )
        return await self.get(cache_key)
    
    async def set_agent_response(self, prompt: str, agent_role: str, model: str, 
                              response: str, ttl: int = 7200) -> bool:
        """Cachea respuesta de agente"""
        cache_key = self._generate_cache_key(
            'agent_response',
            prompt=prompt[:1000],
            agent_role=agent_role,
            model=model
        )
        return await self.set(cache_key, response, ttl)
    
    async def get_debate_summary(self, debate_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene resumen de debate cacheado"""
        cache_key = f"debate_summary:{debate_id}"
        return await self.get(cache_key)
    
    async def set_debate_summary(self, debate_id: str, summary: Dict[str, Any], 
                               ttl: int = 86400) -> bool:
        """Cachea resumen de debate"""
        cache_key = f"debate_summary:{debate_id}"
        return await self.set(cache_key, summary, ttl)
    
    async def get_worker_status(self, worker_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene estado de worker cacheado"""
        cache_key = f"worker_status:{worker_id}"
        return await self.get(cache_key)
    
    async def set_worker_status(self, worker_id: str, status: Dict[str, Any], 
                              ttl: int = 300) -> bool:
        """Cachea estado de worker (TTL corto para frescura)"""
        cache_key = f"worker_status:{worker_id}"
        return await self.set(cache_key, status, ttl)
    
    async def increment_debate_count(self, mode: str) -> Optional[int]:
        """Incrementa contador de debates por modo"""
        cache_key = f"debate_count:{mode}"
        return await self.increment(cache_key)
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Obtiene estado de salud del caché"""
        if not self.enabled:
            return {"status": "disabled", "redis_url": self.redis_url}
        
        try:
            client = await self._get_client()
            if client is None:
                return {"status": "disconnected", "redis_url": self.redis_url}
            
            # Test básico
            start_time = time.time()
            await client.ping()
            latency = (time.time() - start_time) * 1000
            
            # Info de Redis
            info = await client.info()
            
            return {
                "status": "connected",
                "redis_url": self.redis_url,
                "latency_ms": round(latency, 2),
                "memory_used": info.get('used_memory_human', 'unknown'),
                "connected_clients": info.get('connected_clients', 0),
                "total_commands_processed": info.get('total_commands_processed', 0)
            }
        except Exception as e:
            return {
                "status": "error",
                "redis_url": self.redis_url,
                "error": str(e)
            }
    
    async def close(self):
        """Cierra conexión Redis"""
        if self.client:
            await self.client.close()
            logger.info("cache.redis_closed")


# Singleton instance
_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """Obtiene instancia singleton del servicio de caché"""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service

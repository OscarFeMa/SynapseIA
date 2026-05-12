"""
Synapse Council v2.0 - Monitoring API Routes
Endpoints para métricas Prometheus y estado del sistema
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse, JSONResponse
from typing import Dict, Any
import structlog

from backend.monitoring.metrics import get_metrics_collector, get_prometheus_metrics
from backend.services.worker_pool import get_worker_pool
from backend.services.cache_service import get_cache_service

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1/monitoring", tags=["monitoring"])


@router.get("/metrics", response_class=PlainTextResponse)
async def get_metrics():
    """
    Endpoint de métricas en formato Prometheus
    Compatible con Grafana y otros sistemas de monitoreo
    """
    try:
        metrics = get_prometheus_metrics()
        return PlainTextResponse(
            content=metrics,
            media_type="text/plain; version=0.0.4; charset=utf-8"
        )
    except Exception as e:
        logger.error("monitoring.metrics_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to generate metrics")


@router.get("/status", response_model=Dict[str, Any])
async def get_system_status():
    """
    Estado completo del sistema
    Incluye workers, caché, y métricas resumidas
    """
    try:
        # Obtener componentes
        metrics_collector = get_metrics_collector()
        worker_pool = get_worker_pool()
        cache_service = get_cache_service()
        
        # Estado de workers
        worker_status = await worker_pool.get_pool_status()
        
        # Estado de caché
        cache_status = await cache_service.get_health_status()
        
        # Métricas resumidas
        metrics_summary = metrics_collector.get_metrics_summary()
        
        return {
            "status": "healthy",
            "timestamp": logger.info("monitoring.status_requested"),
            "components": {
                "workers": worker_status,
                "cache": cache_status,
                "metrics": metrics_summary
            },
            "health_checks": {
                "workers_healthy": worker_status["healthy_workers"] > 0,
                "cache_connected": cache_status.get("status") == "connected",
                "metrics_available": True
            }
        }
    except Exception as e:
        logger.error("monitoring.status_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get system status")


@router.get("/workers", response_model=Dict[str, Any])
async def get_workers_status():
    """Estado detallado de workers"""
    try:
        worker_pool = get_worker_pool()
        status = await worker_pool.get_pool_status()
        return status
    except Exception as e:
        logger.error("monitoring.workers_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get workers status")


@router.get("/cache", response_model=Dict[str, Any])
async def get_cache_status():
    """Estado del caché Redis"""
    try:
        cache_service = get_cache_service()
        status = await cache_service.get_health_status()
        return status
    except Exception as e:
        logger.error("monitoring.cache_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get cache status")


@router.get("/debates", response_model=Dict[str, Any])
async def get_debates_metrics():
    """Métricas específicas de debates"""
    try:
        metrics_collector = get_metrics_collector()
        summary = metrics_collector.get_metrics_summary()
        
        # Métricas detalladas de debates
        return {
            "total_created": summary.get("debates_total", 0),
            "currently_active": summary.get("active_debates", 0),
            "uptime_seconds": summary.get("uptime_seconds", 0),
            "debates_per_hour": summary.get("debates_per_hour", 0),
            "avg_debate_duration": summary.get("avg_debate_duration", 0),
            "success_rate": summary.get("debate_success_rate", 0)
        }
    except Exception as e:
        logger.error("monitoring.debates_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get debates metrics")


@router.get("/health")
async def health_check():
    """
    Health check simple para load balancers y orquestadores
    """
    try:
        # Verificar componentes críticos
        worker_pool = get_worker_pool()
        cache_service = get_cache_service()
        
        # Estado de workers
        worker_status = await worker_pool.get_pool_status()
        workers_ok = worker_status["healthy_workers"] > 0
        
        # Estado de caché (no crítico)
        cache_status = await cache_service.get_health_status()
        cache_ok = cache_status.get("status") in ["connected", "disabled"]
        
        # Determinar salud general
        overall_healthy = workers_ok  # Workers son críticos
        
        status_code = 200 if overall_healthy else 503
        
        return JSONResponse(
            content={
                "status": "healthy" if overall_healthy else "unhealthy",
                "components": {
                    "workers": "healthy" if workers_ok else "unhealthy",
                    "cache": "healthy" if cache_ok else "unhealthy"
                },
                "checks": {
                    "workers_healthy": workers_ok,
                    "cache_healthy": cache_ok
                }
            },
            status_code=status_code
        )
    except Exception as e:
        logger.error("monitoring.health_error", error=str(e))
        return JSONResponse(
            content={
                "status": "unhealthy",
                "error": str(e)
            },
            status_code=503
        )


@router.post("/workers/{worker_id}/heartbeat")
async def worker_heartbeat(worker_id: str, heartbeat_data: Dict[str, Any]):
    """
    Endpoint para que workers reporten su estado
    """
    try:
        worker_pool = get_worker_pool()
        await worker_pool.update_worker_heartbeat(worker_id)
        
        logger.info("monitoring.worker_heartbeat", 
                   worker_id=worker_id, 
                   data=heartbeat_data)
        
        return {"status": "received", "worker_id": worker_id}
    except Exception as e:
        logger.error("monitoring.heartbeat_error", 
                   worker_id=worker_id, 
                   error=str(e))
        raise HTTPException(status_code=500, detail="Failed to process heartbeat")


@router.get("/config")
async def get_monitoring_config():
    """
    Configuración actual de monitoreo
    """
    try:
        worker_pool = get_worker_pool()
        
        return {
            "metrics": {
                "enabled": True,
                "endpoint": "/api/v1/monitoring/metrics",
                "format": "prometheus"
            },
            "worker_pool": {
                "strategy": worker_pool.strategy.value,
                "health_check_interval": worker_pool.health_check_interval
            },
            "alerts": {
                "worker_failure_threshold": 2,  # Número de fallos consecutivos
                "cache_failure_threshold": 3,
                "debate_failure_threshold": 5
            }
        }
    except Exception as e:
        logger.error("monitoring.config_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get monitoring config")

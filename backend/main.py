"""
Synapse Council v2.0 - FastAPI Application
Punto de entrada principal del backend
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import structlog
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import get_settings
from backend.database.local_db import init_db

# Configurar logging básico para ver en consola
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

# Importar routers
from backend.api.routes.health import router as health_router
from backend.api.routes.sessions import router as sessions_router
from backend.api.routes.websockets import router as websockets_router
from backend.api.routes.network import router as network_router
from backend.api.routes.debate import router as debate_router
from backend.api.routes.system import router as system_router
from backend.api.routes.monitoring_dashboard import router as monitoring_router
from backend.network.discovery import node_discoverer
from backend.network.heartbeat import HeartbeatManager
from backend.network.tcp_handshake import TCPHandshake

# Obtener configuración primero
settings = get_settings()

# Configurar logging estructurado con JSON y trazabilidad
from backend.monitoring.logging_config import setup_logging, get_logger
setup_logging(
    log_level=settings.LOG_LEVEL,
    log_file="logs/synapse.log",
    console_output=True
)
synapse_logger = get_logger()

# Inicializar sistema de alertas proactivas
from backend.monitoring.alerts import init_health_monitoring, shutdown_health_monitoring

# Instancia global de heartbeat manager
heartbeat_manager: HeartbeatManager = None
tcp_handshake: TCPHandshake = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager para startup/shutdown"""
    global heartbeat_manager, tcp_handshake
    
    # Startup
    synapse_logger.info("synapse_council.starting", version="2.1.0", node_role=settings.NODE_ROLE)
    
    # Inicializar base de datos
    await init_db()
    synapse_logger.info("database.initialized", url=settings.DATABASE_URL)
    
    # Iniciar memoria híbrida v2 (condicional)
    try:
        from backend.memory.hybrid_memory_v2 import get_hybrid_memory_v2
        hybrid_mem = get_hybrid_memory_v2()
        await hybrid_mem.start()
        synapse_logger.info("hybrid_memory_v2.started")
    except Exception as e:
        synapse_logger.warning("hybrid_memory_v2.start_failed", error=str(e))
    
    # Iniciar descubrimiento de red
    await node_discoverer.start()
    
    # Iniciar TCP handshake (basado en Pensamiento Coral)
    tcp_handshake = TCPHandshake(role=settings.NODE_ROLE)
    
    # Iniciar heartbeat (basado en Pensamiento Coral)
    if settings.is_master:
        heartbeat_manager = HeartbeatManager(
            role="MASTER",
            interval=settings.HEARTBEAT_INTERVAL,
            timeout=settings.HEARTBEAT_TIMEOUT
        )
        await heartbeat_manager.start()
        synapse_logger.info("heartbeat.started", role="MASTER")
    else:
        # Worker inicia heartbeat cuando conoce la IP del Master
        heartbeat_manager = HeartbeatManager(
            role="WORKER",
            interval=settings.HEARTBEAT_INTERVAL,
            timeout=settings.HEARTBEAT_TIMEOUT
        )
        synapse_logger.info("heartbeat.initialized", role="WORKER")
    
    # Iniciar sistema de alertas proactivas y monitoreo de salud
    await init_health_monitoring()
    synapse_logger.info("health_monitoring.started")
    
    yield
    
    # Shutdown
    await node_discoverer.stop()
    
    # Detener heartbeat
    if heartbeat_manager:
        await heartbeat_manager.stop()
        synapse_logger.info("heartbeat.stopped")
    
    # Cerrar TCP handshake
    if tcp_handshake:
        tcp_handshake.close()
        synapse_logger.info("tcp_handshake.closed")
    
    # Detener memoria híbrida
    try:
        from backend.memory.hybrid_memory_v2 import get_hybrid_memory_v2
        hybrid_mem = get_hybrid_memory_v2()
        await hybrid_mem.stop()
        synapse_logger.info("hybrid_memory_v2.stopped")
    except Exception as e:
        synapse_logger.warning("hybrid_memory_v2.stop_failed", error=str(e))
    
    # Detener sistema de monitoreo de salud
    await shutdown_health_monitoring()
    
    synapse_logger.info("synapse_council.stopping")


app = FastAPI(
    title="Synapse Council v2.1",
    description="Plataforma de razonamiento colectivo híbrido con Tribunal de Magistrados - Con observabilidad mejorada",
    version="2.1.0",
    lifespan=lifespan,
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware de seguridad (Fase 5)
from backend.api.middleware import RateLimitMiddleware, SecurityHeadersMiddleware, LoggingMiddleware

app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=60,
    burst_size=10
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(LoggingMiddleware)


# Registrar routers
app.include_router(health_router)
app.include_router(sessions_router)
app.include_router(websockets_router)
app.include_router(network_router)
app.include_router(debate_router, prefix="/api/v1")
app.include_router(system_router, prefix="/api/v1")
app.include_router(monitoring_router)  # Dashboard de monitoreo

# Debug router (importación local para evitar imports circulares)
from backend.api.routes.debug import router as debug_router
app.include_router(debug_router)
synapse_logger.info("debug_router.enabled")

@app.get("/")
async def root():
    """Endpoint raíz con información del sistema"""
    return {
        "name": "Synapse Council",
        "version": "2.1.0",
        "description": "Plataforma de razonamiento colectivo híbrido",
        "node_role": settings.NODE_ROLE,
        "docs": "/docs",
        "health": "/health",
        "dashboard": "/api/monitoring/dashboard",
        "metrics": "/api/monitoring/metrics/prometheus"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        workers=1
    )

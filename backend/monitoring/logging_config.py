"""
Synapse Council v2.1 - Logging Estructurado JSON
Logging centralizado con trazabilidad distribuida y formato JSON
"""
import logging
import json
import sys
import traceback
from datetime import datetime
from typing import Any, Dict, Optional
import uuid
from contextvars import ContextVar
from pythonjsonlogger import jsonlogger


# ─── Contexto de Trazabilidad Distribuida ─────────────────────
# Trace ID se propaga a través de todas las operaciones
trace_id_var: ContextVar[Optional[str]] = ContextVar('trace_id', default=None)
span_id_var: ContextVar[Optional[str]] = ContextVar('span_id', default=None)


def get_trace_id() -> str:
    """Obtiene o crea un Trace ID para la operación actual"""
    trace_id = trace_id_var.get()
    if not trace_id:
        trace_id = str(uuid.uuid4())
        trace_id_var.set(trace_id)
    return trace_id


def get_span_id() -> str:
    """Obtiene o crea un Span ID para el contexto actual"""
    span_id = span_id_var.get()
    if not span_id:
        span_id = str(uuid.uuid4())[:8]
        span_id_var.set(span_id)
    return span_id


def set_trace_context(trace_id: Optional[str] = None, span_id: Optional[str] = None):
    """Establece contexto de trazabilidad para operaciones correlacionadas"""
    if trace_id:
        trace_id_var.set(trace_id)
    if span_id:
        span_id_var.set(span_id)


def clear_trace_context():
    """Limpia el contexto de trazabilidad"""
    trace_id_var.set(None)
    span_id_var.set(None)


# ─── Formatter JSON Personalizado ─────────────────────────────
class SynapseJsonFormatter(jsonlogger.JsonFormatter):
    """Formatter JSON enriquecido con metadata de Synapse"""
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]):
        super().add_fields(log_record, record, message_dict)
        
        # Metadata de trazabilidad
        log_record['trace_id'] = get_trace_id()
        log_record['span_id'] = get_span_id()
        
        # Timestamp ISO 8601
        log_record['timestamp'] = datetime.utcnow().isoformat() + 'Z'
        
        # Nivel de log
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        
        # Ubicación del código
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['line'] = record.lineno
        
        # Host info
        log_record['hostname'] = socket.gethostname() if 'socket' in globals() else 'unknown'
        
        # Agregar campos personalizados si existen
        for key, value in message_dict.items():
            if key not in log_record:
                log_record[key] = value
        
        # Manejo de excepciones
        if record.exc_info:
            log_record['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else 'Unknown',
                'message': str(record.exc_info[1]) if record.exc_info[1] else '',
                'traceback': traceback.format_exception(*record.exc_info)
            }


# ─── Logger Centralizado ──────────────────────────────────────
class SynapseLogger:
    """Logger centralizado para todo el sistema Synapse"""
    
    _instance: Optional['SynapseLogger'] = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, log_level: str = "INFO", log_file: Optional[str] = None, console_output: bool = True):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self.logger = logging.getLogger('synapse')
        self.logger.setLevel(getattr(logging, log_level.upper()))
        self.logger.handlers.clear()
        
        # Formatter JSON
        json_formatter = SynapseJsonFormatter(
            '%(timestamp)s %(level)s %(logger)s %(trace_id)s %(span_id)s %(message)s'
        )
        
        # Handler de consola (si está habilitado)
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(json_formatter)
            self.logger.addHandler(console_handler)
        
        # Handler de archivo (si está especificado)
        if log_file:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(json_formatter)
            self.logger.addHandler(file_handler)
    
    def _log(self, level: int, message: str, **kwargs):
        """Método base de logging con contexto enriquecido"""
        extra = {
            'trace_id': get_trace_id(),
            'span_id': get_span_id()
        }
        extra.update(kwargs)
        self.logger.log(level, message, extra=extra)
    
    def debug(self, message: str, **kwargs):
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        self._log(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        self._log(logging.CRITICAL, message, **kwargs)
    
    def exception(self, message: str, **kwargs):
        """Log de excepción con traceback completo"""
        self._log(logging.ERROR, message, exc_info=True, **kwargs)
    
    def audit(self, action: str, user: str = None, resource: str = None, **kwargs):
        """Log de auditoría para acciones críticas"""
        self.info(
            f"AUDIT: {action}",
            audit_action=action,
            audit_user=user,
            audit_resource=resource,
            audit_type=True,
            **kwargs
        )
    
    def performance(self, operation: str, duration_ms: float, **kwargs):
        """Log de métricas de performance"""
        self.info(
            f"PERF: {operation}",
            performance_operation=operation,
            performance_duration_ms=duration_ms,
            performance_type=True,
            **kwargs
        )
    
    def security(self, event: str, source_ip: str = None, user: str = None, **kwargs):
        """Log de eventos de seguridad"""
        self.warning(
            f"SECURITY: {event}",
            security_event=event,
            security_source_ip=source_ip,
            security_user=user,
            security_type=True,
            **kwargs
        )


# ─── Decoradores para Trazabilidad ────────────────────────────
def traceable(func):
    """Decorador para agregar trazabilidad automática a funciones"""
    import functools
    
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        # Crear nuevo span para esta función
        parent_trace_id = get_trace_id()
        parent_span_id = get_span_id()
        
        new_span_id = str(uuid.uuid4())[:8]
        span_id_var.set(new_span_id)
        
        try:
            result = await func(*args, **kwargs)
            return result
        except Exception as e:
            raise
        finally:
            # Restaurar contexto padre
            trace_id_var.set(parent_trace_id)
            span_id_var.set(parent_span_id)
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        # Crear nuevo span para esta función
        parent_trace_id = get_trace_id()
        parent_span_id = get_span_id()
        
        new_span_id = str(uuid.uuid4())[:8]
        span_id_var.set(new_span_id)
        
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            raise
        finally:
            # Restaurar contexto padre
            trace_id_var.set(parent_trace_id)
            span_id_var.set(parent_span_id)
    
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper


# ─── Inicialización ───────────────────────────────────────────
import socket

def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = "logs/synapse.log",
    console_output: bool = True
) -> SynapseLogger:
    """Configura el sistema de logging global"""
    logger_instance = SynapseLogger(
        log_level=log_level,
        log_file=log_file,
        console_output=console_output
    )
    return logger_instance


# Singleton global
_global_logger: Optional[SynapseLogger] = None


def get_logger() -> SynapseLogger:
    """Obtiene el logger global"""
    global _global_logger
    if _global_logger is None:
        _global_logger = SynapseLogger()
    return _global_logger


# Alias para compatibilidad
logger = get_logger()

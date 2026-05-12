# Synapse Council v2.1 - Optimizaciones Críticas Implementadas

## Resumen Ejecutivo

Se han implementado optimizaciones críticas en los aspectos más sensibles del sistema Synapse Council, enfocándose en seguridad, robustez de conexiones, y automatización del despliegue de workers.

---

## 1. SEGURIDAD MEJORADA

### 1.1 Token SYNAPSE_SECRET_TOKEN Configurable

**Archivo:** `backend/config.py`

**Cambios:**
- El token ahora se lee desde variable de entorno `SYNAPSE_SECRET_TOKEN`
- Se mantiene un valor default solo para desarrollo
- Validador que emite warning en producción si se usa el token default
- Campo `FORCE_TOKEN_CHANGE` para forzar cambio en production

**Código:**
```python
SYNAPSE_SECRET_TOKEN: str = Field(
    default_factory=lambda: os.getenv("SYNAPSE_SECRET_TOKEN", "synapse_coral_2024")
)
FORCE_TOKEN_CHANGE: bool = Field(default=False)

@field_validator("SYNAPSE_SECRET_TOKEN", mode="after")
@classmethod
def validate_token(cls, v):
    if v == "synapse_coral_2024" and os.getenv("ENVIRONMENT") == "production":
        import warnings
        warnings.warn(
            "SYNAPSE_SECRET_TOKEN usa valor default en producción. "
            "Cambia la variable de entorno inmediatamente."
        )
    return v
```

### 1.2 Autenticación en Heartbeat

**Archivo:** `backend/network/heartbeat.py`

**Cambios:**
- El Worker incluye el token en cada mensaje HEARTBEAT
- El Master valida el token antes de aceptar la conexión
- Rechazo inmediato con cierre de conexión si el token es inválido

**Flujo:**
1. Worker envía: `{"type": "HEARTBEAT", "token": "...", "health_score": 100.0}`
2. Master valida token contra `settings.SYNAPSE_SECRET_TOKEN`
3. Si inválido: cierra conexión y loguea `heartbeat.auth_failed`

---

## 2. HEARTBEAT ROBUSTO CON HEALTH SCORE

### 2.1 Sistema de Health Score Dinámico (0-100)

**Archivo:** `backend/network/heartbeat.py`

**Atributos nuevos:**
```python
self._health_score = 100.0  # Score inicial
self._reconnect_attempts = 0
self._max_reconnect_attempts = 5
self._consecutive_failures = 0
self._max_consecutive_failures = 3
```

### 2.2 Degradación y Recuperación Gradual

**Eventos que degradan el score:**
- Timeout de conexión: -5 puntos
- Error de envío: -10 puntos
- Timeout de heartbeat recibido: -15 puntos

**Eventos que recuperan el score:**
- Conexión exitosa: +10 puntos
- Heartbeat enviado exitosamente: resetea fallos consecutivos
- Heartbeat recibido dentro del timeout: +2 puntos (hasta 100)

### 2.3 Backoff Exponencial en Reconexiones

```python
backoff = min(2 ** self._reconnect_attempts, 30)  # Máximo 30s
```

**Comportamiento:**
- Intento 1: 2s de espera
- Intento 2: 4s de espera
- Intento 3: 8s de espera
- Intento 4: 16s de espera
- Intento 5+: 30s de espera (máximo)

### 2.4 Límites de Reintentos

| Parámetro | Valor | Acción al exceder |
|-----------|-------|-------------------|
| `_max_reconnect_attempts` | 5 | Notifica `on_connection_lost` y rompe bucle |
| `_max_consecutive_failures` | 3 | Notifica `on_connection_lost` |

### 2.5 Método is_alive() Mejorado

```python
def is_alive(self) -> bool:
    if not self.last_heartbeat:
        return False
    
    elapsed = (datetime.now() - self.last_heartbeat).total_seconds()
    return elapsed < self.timeout and self._health_score > 50.0
```

**Criterio:** Un peer está vivo solo si:
- Último heartbeat fue hace menos del timeout (15s)
- Health score es mayor a 50

### 2.6 Método get_health_score()

Nuevo método público para consultar el estado de la conexión:
```python
def get_health_score(self) -> float:
    return self._health_score
```

---

## 3. WORKER STARTER MEJORADO

### 3.1 Múltiples Rutas de Búsqueda

**Archivo:** `backend/services/worker_starter.py`

**Rutas soportadas:**
1. `D:\Synapse04_05_26` (ruta original)
2. `C:\SynapseIA` (ruta alternativa común)
3. `%USERPROFILE%\SynapseIA` (ruta por usuario)

**Script PowerShell mejorado:**
```powershell
$paths = @(
    "D:\Synapse04_05_26",
    "C:\SynapseIA",
    "$env:USERPROFILE\SynapseIA"
)

$started = $false
foreach ($path in $paths) {
    if (Test-Path $path) {
        Start-Process python -ArgumentList "-m","backend.main" `
            -WorkingDirectory $path -WindowStyle Hidden
        Write-Output "STARTED:$path"
        $started = $true
        break
    }
}
```

### 3.2 Variables de Entorno Persistentes

**Cambio crítico:** De variables temporales (`$env:`) a persistentes (nivel Machine):

```powershell
[Environment]::SetEnvironmentVariable("NODE_ROLE", "WORKER", "Machine")
[Environment]::SetEnvironmentVariable("WORKER_HOST", "{worker_ip}", "Machine")
```

**Beneficios:**
- Las variables persisten tras reinicios
- Disponibles para todos los procesos del sistema
- No se pierden al cerrar la sesión de PowerShell

### 3.3 Mejor Logging y Reporte de Errores

- Log del path específico donde se inició: `worker_starter.winrm_success output=STARTED:C:\SynapseIA`
- Reporte detallado de stderr truncado (200 chars)
- Manejo de errores con `ErrorActionPreference = "Stop"`

---

## 4. RDP MANAGER SEGURO

### 4.1 Sanitización de Hostnames

**Archivo:** `backend/services/rdp_manager.py`

**Validaciones:**
- IPs IPv4 válidas (octetos 0-255)
- Hostnames alfanuméricos con guiones (RFC 952)
- Rechazo de caracteres especiales y paths relativos

**Regex de validación:**
```python
# IP válida
ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'

# Hostname válido
hostname_pattern = r'^[a-zA-Z0-9][a-zA-Z0-9\-]{0,62}(\.[a-zA-Z0-9][a-zA-Z0-9\-]{0,62})*$'
```

### 4.2 Prevención de Command Injection

- **Sin `shell=True`**: Todos los subprocess usan listas de argumentos
- **Sin interpolación directa**: Los inputs se pasan como argumentos separados
- **Excepciones específicas:** `RDPSecurityError`, `RDPRateLimitError`

### 4.3 Rate Limiting Integrado

```python
RDP_RATE_LIMIT_SECONDS: int = 60  # Mínimo entre conexiones
```

**Implementación:**
- Diccionario en memoria `_last_wake_attempt`
- Identificador por hostname/IP o custom
- Excepción `RDPRateLimitError` si se excede

---

## 5. ARQUITECTURA ASYNC

### 5.1 Consistencia Asyncio

Todo el sistema usa asyncio nativo:
- `async def` para todas las operaciones I/O
- `await` para llamadas asíncronas
- `asyncio.create_task()` para background tasks
- `asyncio.wait_for()` para timeouts
- `asyncio.Lock()` para sincronización

### 5.2 Compatibilidad FastAPI/uvloop

- Sin bloqueos del event loop
- Sin threading innecesario
- Executor solo para comandos subprocess inevitables
- Cancelación correcta de tareas con `asyncio.CancelledError`

---

## 6. PRUEBAS DE VERIFICACIÓN

**Script:** `scripts/test_optimizations.py`

**Tests ejecutados:**
1. ✓ Configuración y seguridad del token
2. ✓ Heartbeat Manager con health score
3. ✓ Worker Auto-Starter mejorado
4. ✓ RDP Manager seguro
5. ✓ Integración completa del sistema

**Resultado:** TODOS LOS TESTS PASARON EXITOSAMENTE

---

## 7. RECOMENDACIONES DE DESPLIEGUE

### 7.1 Producción

```bash
# Variables de entorno obligatorias
export ENVIRONMENT=production
export SYNAPSE_SECRET_TOKEN="tu_token_seguro_de_32_caracteres"
export NODE_ROLE="MASTER"  # o "WORKER"
```

### 7.2 Monitoreo

El health score permite monitoreo proactivo:
- Score < 75: Investigar latencia de red
- Score < 50: is_alive() retorna False, considerar reconexión
- Score < 25: Alerta crítica, posible pérdida de conexión

### 7.3 Troubleshooting

**Logs clave:**
- `heartbeat.auth_failed`: Token incorrecto
- `heartbeat.max_reconnect_attempts_reached`: Problema de conectividad persistente
- `heartbeat.consecutive_failures_exceeded`: Inestabilidad de red
- `worker_starter.winrm_failed`: Verificar WinRM habilitado en Worker
- `rdp_manager.security_error`: Intento de injection detectado

---

## 8. ARCHIVOS MODIFICADOS

| Archivo | Cambios Principales |
|---------|---------------------|
| `backend/config.py` | Token configurable, validador de producción |
| `backend/network/heartbeat.py` | Health score, autenticación, backoff, límites |
| `backend/services/worker_starter.py` | Múltiples rutas, variables persistentes |
| `backend/services/rdp_manager.py` | (Ya tenía sanitización, se mantuvo) |
| `scripts/test_optimizations.py` | Script de tests nuevo |

---

**Versión:** Synapse Council v2.1  
**Fecha:** 2026-05-12  
**Estado:** ✅ Completado y Verificado

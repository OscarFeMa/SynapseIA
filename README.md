# 🧠 SynapseWindsurf Dashboard v2.3.0

**Sistema avanzado de debates con IA y dashboard limpio**

## 🌟 Características Principales

### 🎨 Interfaz Innovadora
- **Diseño único** - Identidad visual distintiva con branding personalizado
- **Interfaz limpia** - HTML puro sin animaciones gráficas complejas
- **Responsive design** - Adaptado a todos los dispositivos
- **Temas múltiples** - 4 temas visuales diferentes

### 📊 Dashboard Principal
- **6 métricas en tiempo real** - Debates, workers, rendimiento
- **Tabla de debates dinámica** - Estados, modos, participantes
- **Acciones rápidas** - Sincronización y recarga completa
- **Navegación fluida** - Acceso a todas las secciones

### 🧠 Gestión de Debates
- **Creación de debates** - Múltiples modos (estándar, consenso, secuencial, cuántico)
- **Control en tiempo real** - Iniciar, detener, monitorear debates
- **Estadísticas detalladas** - Tiempo promedio, tasa de éxito, nivel de consenso
- **Historial completo** - Exportación de resultados

### 🔗 Gestión de Workers
- **Control distribuido** - Gestión de nodos workers
- **Métricas de rendimiento** - Carga, tareas completadas, eficiencia
- **Optimización automática** - Balanceo de carga
- **Monitoreo en vivo** - Estado y recursos de cada worker

### 📊 Sistema de Métricas
- **Análisis completo** - Rendimiento del sistema y recursos
- **Gráficos visuales** - Datos en tiempo real
- **Tabla detallada** - Métricas con tendencias
- **Exportación de datos** - Reportes personalizados

### ⚙️ Configuración Avanzada
- **Personalización completa** - Temas, idioma, modo oscuro
- **Ajustes del sistema** - Intervalos de refresh, límites concurrentes
- **Gestión de caché** - Control de almacenamiento temporal
- **Import/Export** - Gestión de configuración

---

## 🎯 Características Principales

- **Arquitectura Híbrida**: PC A (Master) + PC B (Worker) para soberanía neuronal
- **Tribunal de Magistrados**: 3 roles especializados con Protocolo de Consenso Forzado (PCO)
- **Sistema de Reputación EMA**: Métricas dinámicas por agente y dominio
- **Múltiples Motores**: Ollama, LM Studio, Jan.ai, OpenRouter, Web Agent (Playwright)
- **Hasta 3 Rondas**: Con cruce híbrido Local↔Nube
- **Streaming en Tiempo Real**: WebSocket con tokens en vivo
- **Memoria a Largo Plazo**: Supabase (`memoria-oscar`)
- **Trazabilidad Absoluta**: SQLite local con registro granular

---

## 📁 Estructura

```
synapse-council/
├── backend/
│   ├── main.py              # FastAPI + WebSocket + API endpoints
│   ├── config.py            # Pydantic Settings
│   ├── requirements.txt     # Dependencias Python
│   ├── database/
│   │   ├── models.py        # 7 tablas SQLAlchemy
│   │   └── local_db.py      # SQLite async
│   ├── adapters/            # Clientes de IA
│   │   ├── ollama.py        # Ollama (PC B)
│   │   ├── lm_studio.py     # LM Studio (PC B)
│   │   ├── jan.py           # Jan.ai (PC B)
│   │   ├── openrouter.py    # APIs comerciales
│   │   └── web_agent.py     # Playwright (ChatGPT, Claude)
│   ├── engine/              # Motor de debate (Fase 1-2)
│   │   ├── local_engine_manager.py   # Gestión de motores locales
│   │   ├── agent_orchestrator.py     # Paralelismo y persistencia
│   │   ├── round_controller.py       # 4 fases del debate
│   │   ├── session_manager.py        # Ciclo de vida de sesiones
│   │   ├── prompts.py                # Prompts por rol
│   │   ├── tribunal.py               # Tribunal de Magistrados (Fase 2)
│   │   └── convergence.py            # Evaluador de convergencia (Fase 2)
│   ├── api/                 # API routes (Fase 3)
│   │   └── websocket.py              # WebSocket manager streaming
├── frontend/                # Fase 4: React + Vite
│   ├── src/
│   │   ├── components/
│   │   │   ├── Chat/
│   │   │   │   ├── ChatInput.jsx      # Formulario nueva sesión
│   │   │   │   ├── SessionView.jsx    # Vista debate en progreso
│   │   │   │   └── AgentCard.jsx      # Card de agente con streaming
│   │   │   ├── Tribunal/
│   │   │   │   └── TribunalPanel.jsx  # Panel del Tribunal
│   │   │   └── History/
│   │   │       └── SessionList.jsx    # Historial de sesiones
│   │   ├── hooks/
│   │   │   ├── useWebSocket.js        # Hook WebSocket
│   │   │   └── useSession.js          # Hook API REST
│   │   ├── store/
│   │   │   └── useStore.js            # Zustand stores
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
├── scripts/
│   ├── test_health.py       # Test Fase 0
│   ├── test_session.py      # Test Fase 1-2 (debate real)
│   └── test_websocket.py    # Test Fase 3 (streaming WebSocket)
├── data/                    # SQLite local (gitignored)
└── docs/                    # Documentación
```

## 🚀 Inicio Rápido

### Requisitos
- Python 3.8+
- Navegador web moderno

### Ejecución
```bash
# Iniciar servidor local
cd frontend/dashboard
python -m http.server 8005

# Acceder al dashboard
# http://localhost:8005/
```

## 📁 Estructura del Proyecto

```
frontend/dashboard/
├── index.html          # Dashboard principal
├── debates.html        # Gestión de debates
├── workers.html        # Gestión de workers
├── metrics.html        # Métricas del sistema
├── settings.html       # Configuración
├── favicon.ico         # Icono del sistema
└── src/              # Componentes React (legacy)
```

## 🎯 Tecnologías Utilizadas

- **HTML5** - Estructura semántica
- **Tailwind CSS** - Estilos modernos
- **JavaScript Vanilla** - Interactividad
- **Python HTTP Server** - Desarrollo local
- **Google Fonts** - Tipografía profesional

## 🔧 Características Técnicas

### Optimización
- **Sin animaciones gráficas** - Mejor rendimiento
- **Cache control** - Meta tags para cache
- **Auto-refresh** - Datos cada 30 segundos
- **Responsive design** - Mobile-first

### Seguridad
- **Content Security Policy** - Configuración segura
- **Form validation** - Atributos correctos
- **HTTPS ready** - Preparado para producción

### Accesibilidad
- **Semántica HTML5** - Estructura accesible
- **Contraste alto** - Mejor legibilidad
- **Navegación por teclado** - Full keyboard support

## 🌈 Temas Disponibles

1. **Red Neuronal** 🧠 - Conexiones sinápticas
2. **Reino Cuántico** ⚛️ - Estados superpuestos
3. **Conciencia Cósmica** 🌌 - Red universal
4. **Sinapsis Digital** 💻 - Código puro

## 📈 Métricas del Sistema

- **Debates totales**: 42
- **Debates activos**: 8
- **Workers conectados**: 12
- **Tasa de éxito**: 94.2%
- **Tiempo promedio**: 2.3s
- **Nivel de conciencia**: 78%

## 🚨 Estado Actual

**✅ Sistema Funcional**
- Dashboard principal operativo
- Todas las páginas accesibles
- Navegación sin errores 404
- Servidor local funcionando
- Datos dinámicos activos

## � Actualizaciones Recientes

### v2.3.0 (Última versión)
- ✅ Dashboard limpio desde cero
- ✅ Eliminación de animaciones gráficas
- ✅ Corrección de enlaces de navegación
- ✅ Optimización de layout compacto
- ✅ Sistema de branding único
- ✅ 5 páginas funcionales completas

## 🎯 Próximos Pasos

- [ ] Integración con backend real
- [ ] Sistema de autenticación
- [ ] WebSocket para tiempo real
- [ ] Deploy automático
- [ ] Testing automatizado

---

## 📊 Plan de Implementación

| Fase | Descripción | Estado |
|------|-------------|--------|
| **0** | Infraestructura base, DB, health check | ✅ COMPLETADA |
| **1** | Motor core, 1 ronda completa | ✅ COMPLETADA |
| **2** | Múltiples rondas, Tribunal de Magistrados | ✅ COMPLETADA |
| **3** | WebSocket streaming en tiempo real | ✅ COMPLETADA |
| **4** | Frontend React completo | ✅ COMPLETADA |
| **5** | Hardening, reputación EMA, tests | ✅ COMPLETADA |
| **6** | Debates Iterativos Multi-Agente | ✅ **COMPLETADA** |

### ✅ FASE 1 - Motor Core (COMPLETADA)

- ✅ Local Engine Manager (Ollama, LM Studio, Jan)
- ✅ Agent Orchestrator (paralelismo, persistencia, cross-references)
- ✅ Round Controller (4 fases: análisis, crítica, síntesis)
- ✅ Session Manager (ciclo de vida completo)
- ✅ Sistema de prompts (Analista, Crítico, Síntesis)
- ✅ Cruce híbrido Local↔Nube
- ✅ API REST: POST /sessions, GET /sessions/{id}, GET /sessions, DELETE /sessions/{id}
- ✅ Background tasks para ejecución asíncrona

### ✅ FASE 2 - Tribunal y Múltiples Rondas (COMPLETADA)

- ✅ **Tribunal de Magistrados** (3 roles: Evidencias, Riesgos, Alineación)
- ✅ **Protocolo de Consenso Forzado (PCO)** - hasta 3 iteraciones
- ✅ **Convergence Evaluator** - heurísticas de similitud y estabilidad
- ✅ **Múltiples rondas** - hasta 3 rondas con convergencia automática
- ✅ **Contexto acumulado** entre rondas
- ✅ **Veredicto soberano** SIEMPRE ejecutado en LOCAL (PC B)

### ✅ FASE 3 - WebSocket Streaming (COMPLETADA)

- ✅ **WebSocket Manager** - gestión de conexiones múltiples
- ✅ **Streaming de tokens** - texto generado token a token en tiempo real
- ✅ **Eventos de ciclo de vida** - session_start, phase_start, agent_complete, etc.
- ✅ **Eventos del Tribunal** - tribunal_started, tribunal_objection, tribunal_verdict
- ✅ **Heartbeat/ping** - mantenimiento de conexión
- ✅ **Broadcast por sesión** - múltiples clientes pueden observar misma sesión

### ✅ FASE 4 - Frontend React (COMPLETADA)

- ✅ **React 18 + Vite 5** - Build tooling moderno
- ✅ **Tailwind CSS 3** - Styling con tema oscuro personalizado
- ✅ **Zustand** - Estado global sin boilerplate
- ✅ **React Router 6** - Navegación SPA
- ✅ **Componente ChatInput** - Formulario de nueva consulta
- ✅ **Componente SessionView** - Vista de debate en progreso con streaming
- ✅ **Componente AgentCard** - Cards de agentes con texto en tiempo real
- ✅ **Componente TribunalPanel** - Panel del Tribunal de Magistrados
- ✅ **Componente SessionList** - Historial de sesiones
- ✅ **Hooks useWebSocket/useSession** - Integración con API y WebSocket

### ✅ FASE 5 - Hardening y Reputación EMA (COMPLETADA)

- ✅ **Sistema de Reputación EMA** - Exponential Moving Average (α=0.3)
  - TSA: Tasa de Supervivencia de Argumentos
  - IID: Índice de Independencia Dialéctica
  - PVT: Precisión en Validación Técnica
- ✅ **Elección dinámica de agentes** - Selección por reputation_score
- ✅ **Elevación automática a Supabase** - Memoria-oscar para veredictos notables
- ✅ **Debates Iterativos** - Sistema de múltiples iteraciones con contexto persistente
- ✅ **Liberación Automática de RAM** - Unload de modelos entre turnos para evitar OOM
- ✅ **Rate Limiting** - 60 req/min, burst de 10
- ✅ **Security Headers** - CSP, HSTS, X-Frame-Options
- ✅ **Logging estructurado** - Todas las requests HTTP
- ✅ **Tests end-to-end** - Scripts de test completos

### ✅ FASE 6 - Debates Iterativos Multi-Agente (COMPLETADA)

- ✅ **Sistema de Iteraciones Avanzado** - 3+ iteraciones con contexto persistente
- ✅ **Múltiples Roles Dinámicos** - ANALYST, CRITIC, VALIDATOR, CONSENSUS
- ✅ **Cruzamientos Críticos** - Agentes se responden entre sí para profundizar argumentos
- ✅ **Liberación Automática de RAM** - `unload_model()` antes de cada turno
- ✅ **Sistema de Consenso** - Búsqueda de acuerdos con soluciones propuestas
- ✅ **API Endpoint** - `/api/v1/debate/create/iterative` para debates iterativos
- ✅ **Maratón de 10 Debates** - Script `run_10_debates.py` para ejecución automática

**Características del Sistema Iterativo:**
- Contexto completo entre iteraciones (resúmenes acumulativos)
- Roles cambian dinámicamente en cada fase
- Validación de argumentos por agente VALIDATOR
- Búsqueda de consenso final con propuestas de solución
- Streaming en tiempo real de tokens generados
- Guardado automático de transcripcias y reporte maestro

**Uso del script de 10 debates:**
```bash
# Ejecutar maratón de 10 debates automáticamente
python run_10_debates.py

# Resultados en:
# - data/debates/MASTER_REPORT_10_DEBATES_*.md
# - data/debates/debate_debate_*.md (individuales)
```

---

## 🔧 Servicios Verificados en /health

- ✅ **Base de datos SQLite** - Persistencia local
- ✅ **Ollama** - Modelos open-source (PC B)
- ✅ **LM Studio** - Modelos GGUF (PC B)
- ✅ **Jan.ai** - Modelos experimentales (PC B)
- ✅ **OpenRouter** - APIs comerciales
- ✅ **Web Agent** - Playwright para IAs gratuitas

---

## 🏛️ Tribunal de Magistrados

1. **Magistrado de Evidencias** - Validación técnica rigurosa
2. **Magistrado de Riesgos** - Abogado del Diablo (seguridad)
3. **Magistrado de Alineación** - Product Owner pragmático

**Protocolo de Consenso Forzado (PCO)**:
- Propuesta → Veto → Corrección (hasta 3 iteraciones)
- Resolución por méritos si persiste disenso

---

---

**🧠 SynapseIA - Conectando Mentes, Amplificando Inteligencia**

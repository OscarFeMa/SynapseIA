"""
Synapse Council v2.1 - Dashboard de Estado en Tiempo Real
API para monitoreo visual del sistema
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime
import psutil
import asyncio

from backend.config import get_settings, Settings
from backend.monitoring.metrics import get_metrics_collector, get_prometheus_metrics


router = APIRouter(prefix="/monitoring", tags=["monitoring"])


def get_heartbeat_manager():
    """Obtiene el heartbeat manager global evitando import circular"""
    from backend.main import heartbeat_manager
    return heartbeat_manager


# ─── Modelos de Datos ─────────────────────────────────────────
class WorkerStatus(BaseModel):
    worker_id: str
    host: str
    is_alive: bool
    health_score: float
    last_heartbeat: datetime
    services: Dict[str, bool]
    latency_ms: float


class SystemMetrics(BaseModel):
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_total_gb: float
    disk_percent: float
    uptime_seconds: float
    active_connections: int


class DebateMetrics(BaseModel):
    total_debates: int
    active_debates: int
    completed_debates: int
    failed_debates: int
    avg_duration_seconds: float
    debates_per_minute: float


class AgentMetrics(BaseModel):
    total_calls: int
    success_rate: float
    avg_latency_ms: float
    tokens_generated: int
    calls_by_provider: Dict[str, int]


class DashboardData(BaseModel):
    timestamp: datetime
    system: SystemMetrics
    workers: List[WorkerStatus]
    debates: DebateMetrics
    agents: AgentMetrics
    alerts: List[Dict[str, Any]]
    version: str


# ─── Endpoints del Dashboard ──────────────────────────────────

@router.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard_html():
    """Retorna el dashboard HTML en tiempo real"""
    
    html_content = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Synapse Council - Dashboard</title>
    <style>
        :root {
            --primary: #6366f1;
            --success: #22c55e;
            --warning: #f59e0b;
            --danger: #ef4444;
            --bg: #0f172a;
            --card-bg: #1e293b;
            --text: #f1f5f9;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: var(--bg);
            color: var(--text);
            padding: 20px;
        }
        
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            padding: 20px;
            background: var(--card-bg);
            border-radius: 12px;
            border-left: 4px solid var(--primary);
        }
        
        .header h1 {
            font-size: 24px;
            font-weight: 600;
        }
        
        .timestamp {
            color: #94a3b8;
            font-size: 14px;
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .card {
            background: var(--card-bg);
            border-radius: 12px;
            padding: 20px;
            transition: transform 0.2s;
        }
        
        .card:hover {
            transform: translateY(-2px);
        }
        
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid #334155;
        }
        
        .card-title {
            font-size: 16px;
            font-weight: 600;
            color: #94a3b8;
        }
        
        .metric-value {
            font-size: 32px;
            font-weight: 700;
            color: var(--primary);
        }
        
        .metric-label {
            font-size: 14px;
            color: #94a3b8;
            margin-top: 5px;
        }
        
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        
        .status-alive {
            background: var(--success);
            box-shadow: 0 0 8px var(--success);
        }
        
        .status-dead {
            background: var(--danger);
        }
        
        .worker-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px;
            background: #0f172a;
            border-radius: 8px;
            margin-bottom: 10px;
        }
        
        .worker-info {
            display: flex;
            align-items: center;
        }
        
        .health-bar {
            width: 100px;
            height: 8px;
            background: #334155;
            border-radius: 4px;
            overflow: hidden;
        }
        
        .health-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--danger), var(--warning), var(--success));
            transition: width 0.3s;
        }
        
        .alert {
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 10px;
            border-left: 4px solid;
        }
        
        .alert-warning {
            background: rgba(245, 158, 11, 0.1);
            border-color: var(--warning);
        }
        
        .alert-danger {
            background: rgba(239, 68, 68, 0.1);
            border-color: var(--danger);
        }
        
        .progress-ring {
            width: 120px;
            height: 120px;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .live-indicator {
            animation: pulse 2s infinite;
            color: var(--success);
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="header">
        <div>
            <h1>🧠 Synapse Council Dashboard</h1>
            <p style="color: #94a3b8; margin-top: 5px;">Monitoreo en Tiempo Real del Sistema</p>
        </div>
        <div style="text-align: right;">
            <div class="timestamp" id="timestamp">--</div>
            <div class="live-indicator" style="margin-top: 5px;">● LIVE</div>
        </div>
    </div>
    
    <div class="grid">
        <!-- System Metrics -->
        <div class="card">
            <div class="card-header">
                <span class="card-title">SYSTEM RESOURCES</span>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                <div>
                    <div class="metric-value" id="cpu-usage">--%</div>
                    <div class="metric-label">CPU Usage</div>
                </div>
                <div>
                    <div class="metric-value" id="memory-usage">--%</div>
                    <div class="metric-label">Memory</div>
                </div>
                <div>
                    <div class="metric-value" id="disk-usage">--%</div>
                    <div class="metric-label">Disk</div>
                </div>
                <div>
                    <div class="metric-value" id="uptime">--</div>
                    <div class="metric-label">Uptime</div>
                </div>
            </div>
        </div>
        
        <!-- Active Debates -->
        <div class="card">
            <div class="card-header">
                <span class="card-title">DEBATE ACTIVITY</span>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                <div>
                    <div class="metric-value" id="active-debates" style="color: var(--success);">0</div>
                    <div class="metric-label">Active Debates</div>
                </div>
                <div>
                    <div class="metric-value" id="total-debates" style="color: #94a3b8; font-size: 24px;">0</div>
                    <div class="metric-label">Total Debates</div>
                </div>
                <div>
                    <div class="metric-value" id="completed-debates" style="color: var(--primary); font-size: 24px;">0</div>
                    <div class="metric-label">Completed</div>
                </div>
                <div>
                    <div class="metric-value" id="failed-debates" style="color: var(--danger); font-size: 24px;">0</div>
                    <div class="metric-label">Failed</div>
                </div>
            </div>
        </div>
        
        <!-- Workers Status -->
        <div class="card">
            <div class="card-header">
                <span class="card-title">WORKERS STATUS</span>
            </div>
            <div id="workers-list">
                <div style="text-align: center; color: #94a3b8; padding: 20px;">
                    Loading workers...
                </div>
            </div>
        </div>
        
        <!-- Agent Performance -->
        <div class="card">
            <div class="card-header">
                <span class="card-title">AGENT PERFORMANCE</span>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                <div>
                    <div class="metric-value" id="agent-calls">0</div>
                    <div class="metric-label">Total Calls</div>
                </div>
                <div>
                    <div class="metric-value" id="success-rate">--%</div>
                    <div class="metric-label">Success Rate</div>
                </div>
                <div>
                    <div class="metric-value" id="avg-latency">--ms</div>
                    <div class="metric-label">Avg Latency</div>
                </div>
                <div>
                    <div class="metric-value" id="tokens-gen">0</div>
                    <div class="metric-label">Tokens Generated</div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Alerts Section -->
    <div class="card" style="margin-bottom: 30px;">
        <div class="card-header">
            <span class="card-title">ACTIVE ALERTS</span>
        </div>
        <div id="alerts-container">
            <div style="text-align: center; color: #94a3b8; padding: 20px;">
                No active alerts
            </div>
        </div>
    </div>
    
    <script>
        async function fetchDashboardData() {
            try {
                const response = await fetch('/api/monitoring/dashboard/data');
                const data = await response.json();
                
                // Update timestamp
                document.getElementById('timestamp').textContent = 
                    new Date(data.timestamp).toLocaleString();
                
                // Update system metrics
                document.getElementById('cpu-usage').textContent = data.system.cpu_percent.toFixed(1) + '%';
                document.getElementById('memory-usage').textContent = data.system.memory_percent.toFixed(1) + '%';
                document.getElementById('disk-usage').textContent = data.system.disk_percent.toFixed(1) + '%';
                
                const hours = Math.floor(data.system.uptime_seconds / 3600);
                const minutes = Math.floor((data.system.uptime_seconds % 3600) / 60);
                document.getElementById('uptime').textContent = `${hours}h ${minutes}m`;
                
                // Update debate metrics
                document.getElementById('active-debates').textContent = data.debates.active_debates;
                document.getElementById('total-debates').textContent = data.debates.total_debates;
                document.getElementById('completed-debates').textContent = data.debates.completed_debates;
                document.getElementById('failed-debates').textContent = data.debates.failed_debates;
                
                // Update workers
                const workersContainer = document.getElementById('workers-list');
                if (data.workers && data.workers.length > 0) {
                    workersContainer.innerHTML = data.workers.map(worker => `
                        <div class="worker-item">
                            <div class="worker-info">
                                <span class="status-indicator ${worker.is_alive ? 'status-alive' : 'status-dead'}"></span>
                                <div>
                                    <div style="font-weight: 600;">${worker.worker_id}</div>
                                    <div style="font-size: 12px; color: #94a3b8;">${worker.host}</div>
                                </div>
                            </div>
                            <div style="text-align: right;">
                                <div style="font-size: 14px; font-weight: 600; color: ${worker.health_score > 70 ? 'var(--success)' : worker.health_score > 40 ? 'var(--warning)' : 'var(--danger)'};">
                                    ${worker.health_score.toFixed(0)}%
                                </div>
                                <div class="health-bar">
                                    <div class="health-fill" style="width: ${worker.health_score}%"></div>
                                </div>
                                <div style="font-size: 11px; color: #94a3b8; margin-top: 4px;">
                                    Last: ${new Date(worker.last_heartbeat).toLocaleTimeString()}
                                </div>
                            </div>
                        </div>
                    `).join('');
                } else {
                    workersContainer.innerHTML = '<div style="text-align: center; color: #94a3b8; padding: 20px;">No workers connected</div>';
                }
                
                // Update agent metrics
                document.getElementById('agent-calls').textContent = data.agents.total_calls;
                document.getElementById('success-rate').textContent = data.agents.success_rate.toFixed(1) + '%';
                document.getElementById('avg-latency').textContent = data.agents.avg_latency_ms.toFixed(0) + 'ms';
                document.getElementById('tokens-gen').textContent = data.agents.tokens_generated.toLocaleString();
                
                // Update alerts
                const alertsContainer = document.getElementById('alerts-container');
                if (data.alerts && data.alerts.length > 0) {
                    alertsContainer.innerHTML = data.alerts.map(alert => `
                        <div class="alert alert-${alert.severity}">
                            <strong>${alert.title}</strong><br>
                            <span style="font-size: 13px;">${alert.message}</span>
                        </div>
                    `).join('');
                } else {
                    alertsContainer.innerHTML = '<div style="text-align: center; color: var(--success); padding: 20px;">✓ All systems operational</div>';
                }
                
            } catch (error) {
                console.error('Error fetching dashboard data:', error);
            }
        }
        
        // Fetch data every 5 seconds
        fetchDashboardData();
        setInterval(fetchDashboardData, 5000);
    </script>
</body>
</html>
    """
    
    return HTMLResponse(content=html_content)


@router.get("/dashboard/data")
async def get_dashboard_data(
    settings: Settings = Depends(get_settings)
) -> DashboardData:
    """Obtiene datos del dashboard en formato JSON"""
    
    # System metrics
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    uptime = datetime.now().timestamp() - psutil.boot_time()
    
    system_metrics = SystemMetrics(
        cpu_percent=cpu_percent,
        memory_percent=memory.percent,
        memory_used_gb=memory.used / (1024**3),
        memory_total_gb=memory.total / (1024**3),
        disk_percent=disk.percent,
        uptime_seconds=uptime,
        active_connections=len(psutil.net_connections())
    )
    
    # Get heartbeat manager data
    try:
        workers_status = []
        heartbeat_manager = get_heartbeat_manager()
        
        if heartbeat_manager and hasattr(heartbeat_manager, 'known_workers'):
            for worker_id, worker_info in heartbeat_manager.known_workers.items():
                workers_status.append(WorkerStatus(
                    worker_id=worker_id,
                    host=worker_info.get('host', 'unknown'),
                    is_alive=worker_info.get('is_alive', False),
                    health_score=worker_info.get('health_score', 0),
                    last_heartbeat=worker_info.get('last_heartbeat', datetime.now()),
                    services=worker_info.get('services', {}),
                    latency_ms=worker_info.get('latency_ms', 0)
                ))
    except Exception:
        workers_status = []
    
    # Metrics collector data
    try:
        metrics_collector = get_metrics_collector()
        summary = metrics_collector.get_metrics_summary()
        
        debate_metrics = DebateMetrics(
            total_debates=int(summary.get('debates_total', 0)),
            active_debates=int(summary.get('active_debates', 0)),
            completed_debates=int(summary.get('completed_debates', 0)),
            failed_debates=int(summary.get('failed_debates', 0)),
            avg_duration_seconds=summary.get('avg_duration', 0),
            debates_per_minute=summary.get('debates_per_minute', 0)
        )
        
        agent_metrics = AgentMetrics(
            total_calls=int(summary.get('agent_calls', 0)),
            success_rate=summary.get('success_rate', 100),
            avg_latency_ms=summary.get('avg_latency', 0),
            tokens_generated=int(summary.get('tokens_generated', 0)),
            calls_by_provider=summary.get('calls_by_provider', {})
        )
    except Exception:
        debate_metrics = DebateMetrics(
            total_debates=0, active_debates=0, completed_debates=0,
            failed_debates=0, avg_duration_seconds=0, debates_per_minute=0
        )
        agent_metrics = AgentMetrics(
            total_calls=0, success_rate=100, avg_latency_ms=0,
            tokens_generated=0, calls_by_provider={}
        )
    
    # Generate alerts
    alerts = []
    
    if cpu_percent > 90:
        alerts.append({
            'severity': 'danger',
            'title': 'High CPU Usage',
            'message': f'CPU usage is at {cpu_percent:.1f}%'
        })
    elif cpu_percent > 70:
        alerts.append({
            'severity': 'warning',
            'title': 'Elevated CPU Usage',
            'message': f'CPU usage is at {cpu_percent:.1f}%'
        })
    
    if memory.percent > 90:
        alerts.append({
            'severity': 'danger',
            'title': 'High Memory Usage',
            'message': f'Memory usage is at {memory.percent:.1f}%'
        })
    
    alive_workers = [w for w in workers_status if w['is_alive']]
    if len(workers_status) > 0 and len(alive_workers) == 0:
        alerts.append({
            'severity': 'danger',
            'title': 'No Workers Alive',
            'message': 'All workers are unresponsive'
        })
    elif len(workers_status) > 0 and len(alive_workers) < len(workers_status):
        alerts.append({
            'severity': 'warning',
            'title': 'Some Workers Down',
            'message': f'{len(workers_status) - len(alive_workers)} worker(s) unresponsive'
        })
    
    return DashboardData(
        timestamp=datetime.now(),
        system=system_metrics,
        workers=workers_status,
        debates=debate_metrics,
        agents=agent_metrics,
        alerts=alerts,
        version="2.1.0"
    )


@router.get("/metrics/prometheus")
async def get_prometheus_metrics_endpoint():
    """Exporta métricas en formato Prometheus para scraping"""
    return Response(
        content=get_prometheus_metrics(),
        media_type="text/plain"
    )


@router.get("/health")
async def health_check():
    """Endpoint de health check simple"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.1.0"
    }


@router.get("/workers")
async def get_workers_status():
    """Obtiene estado detallado de todos los workers"""
    try:
        heartbeat_manager = get_heartbeat_manager()
        if heartbeat_manager and hasattr(heartbeat_manager, 'known_workers'):
            return {"workers": heartbeat_manager.known_workers}
        else:
            return {"workers": {}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

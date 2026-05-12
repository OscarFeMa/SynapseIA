"""
Synapse Council v2.1 - Worker Auto-Starter
Inicia automáticamente el backend del Worker tras detectarlo en la red.
"""
import asyncio
import subprocess
import sys
import time
import structlog
from typing import Optional, Dict, Any
from dataclasses import dataclass

from backend.config import get_settings
from backend.services.rdp_manager import RDPManager

logger = structlog.get_logger()
settings = get_settings()


@dataclass
class WorkerStartResult:
    success: bool
    message: str
    method: str  # "winrm", "rdp", "wmi", "already_running"
    worker_ip: Optional[str] = None
    duration_ms: Optional[int] = None


class WorkerAutoStarter:
    """Gestiona el inicio automático del backend del Worker."""
    
    def __init__(self):
        self._last_attempt = 0
        self._cooldown = 60  # segundos entre intentos
    
    async def start_worker(self, worker_ip: str) -> WorkerStartResult:
        """
        Intenta iniciar el backend del Worker en orden de preferencia:
        1. Verificar si ya está corriendo (health check)
        2. WinRM / PowerShell remoto
        3. WMI (Windows Management Instrumentation)
        4. RDP con script auto-inicio (fallback)
        """
        start_time = time.time()
        
        # Rate limiting
        if time.time() - self._last_attempt < self._cooldown:
            return WorkerStartResult(
                success=False,
                message=f"Cooldown activo. Espera {int(self._cooldown - (time.time() - self._last_attempt))}s",
                method="rate_limited",
                worker_ip=worker_ip
            )
        
        self._last_attempt = time.time()
        
        # 1. Verificar si ya está corriendo
        if await self._is_worker_running(worker_ip):
            return WorkerStartResult(
                success=True,
                message="Worker ya está corriendo",
                method="already_running",
                worker_ip=worker_ip
            )
        
        logger.info("worker_starter.attempting", worker_ip=worker_ip)
        
        # 2. Intentar WinRM / PowerShell remoto
        result = await self._try_winrm(worker_ip)
        if result.success:
            return result
        
        # 3. Intentar WMI
        result = await self._try_wmi(worker_ip)
        if result.success:
            return result
        
        # 4. Fallback: RDP + script
        result = await self._try_rdp(worker_ip)
        if result.success:
            return result
        
        duration_ms = int((time.time() - start_time) * 1000)
        return WorkerStartResult(
            success=False,
            message="Todos los métodos de inicio fallaron",
            method="all_failed",
            worker_ip=worker_ip,
            duration_ms=duration_ms
        )
    
    async def _is_worker_running(self, worker_ip: str) -> bool:
        """Verifica si el Worker ya tiene el backend corriendo."""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Intentar health check en el puerto del Worker
                response = await client.get(f"http://{worker_ip}:8000/health")
                if response.status_code == 200:
                    logger.info("worker_starter.already_running", worker_ip=worker_ip)
                    return True
        except Exception:
            pass
        
        # También verificar Ollama directo
        try:
            import httpx
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(f"http://{worker_ip}:11434/api/tags")
                if response.status_code == 200:
                    # Ollama está corriendo pero no sabemos si Synapse backend
                    logger.info("worker_starter.ollama_running", worker_ip=worker_ip)
                    return False  # Necesitamos iniciar el backend
        except Exception:
            pass
        
        return False
    
    async def _try_winrm(self, worker_ip: str) -> WorkerStartResult:
        """Intenta iniciar el Worker via PowerShell remoto (WinRM)."""
        try:
            logger.info("worker_starter.trying_winrm", worker_ip=worker_ip)
            
            # Comando para iniciar el backend del Worker
            # Asume que el Worker tiene el proyecto en D:\Synapse04_05_26
            ps_script = rf'''
$ErrorActionPreference = "Stop"
$proc = Get-Process python -ErrorAction SilentlyContinue | Where-Object {{$_.CommandLine -like "*backend.main*"}}
if (-not $proc) {{
    [Environment]::SetEnvironmentVariable("NODE_ROLE", "WORKER", "Machine")
    [Environment]::SetEnvironmentVariable("WORKER_HOST", "{worker_ip}", "Machine")
    
    # Intentar múltiples rutas posibles
    $paths = @(
        "D:\Synapse04_05_26",
        "C:\SynapseIA",
        "$env:USERPROFILE\SynapseIA"
    )
    
    $started = $false
    foreach ($path in $paths) {{
        if (Test-Path $path) {{
            Start-Process python -ArgumentList "-m","backend.main" -WorkingDirectory $path -WindowStyle Hidden -ErrorAction SilentlyContinue
            Write-Output "STARTED:$path"
            $started = $true
            break
        }}
    }}
    
    if (-not $started) {{
        Write-Output "ERROR:No valid path found"
    }}
}} else {{
    Write-Output "ALREADY_RUNNING"
}}
'''
            
            # Ejecutar via WinRM usando Invoke-Command
            cmd = [
                "powershell",
                "-Command",
                f"Invoke-Command -ComputerName {worker_ip} -ScriptBlock {{{ps_script}}} -Credential (New-Object System.Management.Automation.PSCredential('{settings.RDP_WORKER_USERNAME}', (ConvertTo-SecureString '{settings.RDP_WORKER_PASSWORD}' -AsPlainText -Force))) -ErrorAction Stop"
            ]
            
            loop = asyncio.get_event_loop()
            proc = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    shell=False
                )
            )
            
            if proc.returncode == 0 and "STARTED" in proc.stdout:
                logger.info("worker_starter.winrm_success", worker_ip=worker_ip)
                
                # Esperar a que el Worker esté listo
                await asyncio.sleep(5)
                if await self._is_worker_running(worker_ip):
                    return WorkerStartResult(
                        success=True,
                        message="Worker iniciado via WinRM",
                        method="winrm",
                        worker_ip=worker_ip
                    )
            
            logger.warning("worker_starter.winrm_failed", worker_ip=worker_ip, returncode=proc.returncode, stderr=proc.stderr[:200])
            
        except subprocess.TimeoutExpired:
            logger.warning("worker_starter.winrm_timeout", worker_ip=worker_ip)
        except FileNotFoundError:
            logger.warning("worker_starter.winrm_not_available", worker_ip=worker_ip)
        except Exception as e:
            logger.error("worker_starter.winrm_error", worker_ip=worker_ip, error=str(e))
        
        return WorkerStartResult(success=False, message="WinRM falló", method="winrm", worker_ip=worker_ip)
    
    async def _try_wmi(self, worker_ip: str) -> WorkerStartResult:
        """Intenta iniciar via WMI (más compatible que WinRM)."""
        try:
            logger.info("worker_starter.trying_wmi", worker_ip=worker_ip)
            
            # Usar wmic para crear proceso remoto
            cmd = [
                "wmic",
                f"/node:{worker_ip}",
                f"/user:{settings.RDP_WORKER_USERNAME}",
                f"/password:{settings.RDP_WORKER_PASSWORD}",
                "process", "call", "create",
                f"cmd /c set NODE_ROLE=WORKER && cd /d D:\\Synapse04_05_26 && python -m backend.main"
            ]
            
            loop = asyncio.get_event_loop()
            proc = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    shell=False
                )
            )
            
            if proc.returncode == 0 and "ProcessId" in proc.stdout:
                logger.info("worker_starter.wmi_success", worker_ip=worker_ip)
                
                await asyncio.sleep(5)
                if await self._is_worker_running(worker_ip):
                    return WorkerStartResult(
                        success=True,
                        message="Worker iniciado via WMI",
                        method="wmi",
                        worker_ip=worker_ip
                    )
            
            logger.warning("worker_starter.wmi_failed", worker_ip=worker_ip, stderr=proc.stderr[:200])
            
        except subprocess.TimeoutExpired:
            logger.warning("worker_starter.wmi_timeout", worker_ip=worker_ip)
        except FileNotFoundError:
            logger.warning("worker_starter.wmic_not_available")
        except Exception as e:
            logger.error("worker_starter.wmi_error", worker_ip=worker_ip, error=str(e))
        
        return WorkerStartResult(success=False, message="WMI falló", method="wmi", worker_ip=worker_ip)
    
    async def _try_rdp(self, worker_ip: str) -> WorkerStartResult:
        """Fallback: Abre RDP y deja un script que se auto-ejecuta."""
        try:
            logger.info("worker_starter.trying_rdp", worker_ip=worker_ip)
            
            # Usar el RDPManager existente
            from backend.services.rdp_manager import RDPManager
            
            result = await RDPManager.connect_to_worker_async(
                hostname=settings.RDP_WORKER_HOSTNAME,
                username=settings.RDP_WORKER_USERNAME,
                password=settings.RDP_WORKER_PASSWORD,
                rate_limit_id="worker_auto_start"
            )
            
            if result.success:
                logger.info("worker_starter.rdp_launched", worker_ip=worker_ip)
                
                # Nota: RDP abre sesión pero no inicia automáticamente el backend
                # El usuario debería tener un script de auto-start en el Worker
                return WorkerStartResult(
                    success=True,
                    message="RDP lanzado. Worker debe tener script de auto-inicio.",
                    method="rdp",
                    worker_ip=worker_ip,
                    duration_ms=result.duration_ms
                )
            
            logger.warning("worker_starter.rdp_failed", worker_ip=worker_ip, message=result.message)
            
        except Exception as e:
            logger.error("worker_starter.rdp_error", worker_ip=worker_ip, error=str(e))
        
        return WorkerStartResult(success=False, message="RDP falló", method="rdp", worker_ip=worker_ip)
    
    async def wait_for_worker_ready(self, worker_ip: str, timeout: int = 120) -> bool:
        """Espera a que el Worker esté listo, haciendo polling."""
        logger.info("worker_starter.waiting", worker_ip=worker_ip, timeout=timeout)
        
        start = time.time()
        while time.time() - start < timeout:
            if await self._is_worker_running(worker_ip):
                logger.info("worker_starter.ready", worker_ip=worker_ip, elapsed=time.time()-start)
                return True
            await asyncio.sleep(2)
        
        logger.warning("worker_starter.timeout", worker_ip=worker_ip, timeout=timeout)
        return False


# Singleton
_worker_starter: Optional[WorkerAutoStarter] = None


def get_worker_starter() -> WorkerAutoStarter:
    """Obtiene instancia singleton del WorkerAutoStarter."""
    global _worker_starter
    if _worker_starter is None:
        _worker_starter = WorkerAutoStarter()
    return _worker_starter

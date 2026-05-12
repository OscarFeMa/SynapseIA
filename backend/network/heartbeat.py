"""
Sistema de Heartbeat basado en Pensamiento Coral - Versión Asyncio.
Permite monitorear la conectividad entre Master y Worker en tiempo real.
MIGRADO de threading a asyncio para compatibilidad con FastAPI/uvloop.
"""
import asyncio
import socket
import json
import structlog
from typing import Optional, Callable
from datetime import datetime

logger = structlog.get_logger()


class HeartbeatManager:
    """Gestor de heartbeat async para monitorear conectividad Master/Worker."""
    
    def __init__(self, role: str, interval: int = 5, timeout: int = 15):
        self.role = role
        self.interval = interval
        self.timeout = timeout
        self.running = False
        self.last_heartbeat: Optional[datetime] = None
        self._task: Optional[asyncio.Task] = None
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._server: Optional[asyncio.Server] = None
        self._stop_event = asyncio.Event()
        self.peer_ip: Optional[str] = None
        self.on_heartbeat_received: Optional[Callable] = None
        self.on_connection_lost: Optional[Callable] = None
        # Mejoras de robustez
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 5
        self._consecutive_failures = 0
        self._max_consecutive_failures = 3
        self._health_score = 100.0  # Score de salud de la conexión (0-100)
        
    async def start(self, peer_ip: Optional[str] = None):
        """Inicia el sistema de heartbeat de forma async."""
        self.peer_ip = peer_ip
        self.running = True
        self.last_heartbeat = datetime.now()
        
        if self.role == "WORKER":
            self._task = asyncio.create_task(self._send_heartbeats())
            logger.info("heartbeat.started", role="WORKER", peer_ip=peer_ip)
        else:
            self._task = asyncio.create_task(self._listen_heartbeats())
            logger.info("heartbeat.started", role="MASTER")
    
    async def stop(self):
        """Detiene el sistema de heartbeat de forma async."""
        self.running = False
        self._stop_event.set()
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        if self._writer:
            self._writer.close()
            try:
                await self._writer.wait_closed()
            except Exception:
                pass
        
        if self._server:
            self._server.close()
            await self._server.wait_closed()
        
        logger.info("heartbeat.stopped")
    
    async def _send_heartbeats(self):
        """Worker envía heartbeats periódicos al Master via asyncio."""
        while self.running and self.peer_ip:
            try:
                if not self._writer:
                    try:
                        # Backoff exponencial para reconexión
                        backoff = min(2 ** self._reconnect_attempts, 30)
                        self._reader, self._writer = await asyncio.wait_for(
                            asyncio.open_connection(self.peer_ip, 54322),
                            timeout=5.0
                        )
                        logger.info("heartbeat.tcp_connected", peer_ip=self.peer_ip)
                        self._reconnect_attempts = 0  # Resetear tras éxito
                        self._health_score = min(100.0, self._health_score + 10)
                    except asyncio.TimeoutError:
                        logger.warning("heartbeat.tcp_connect_timeout", peer_ip=self.peer_ip, attempt=self._reconnect_attempts)
                        self._reconnect_attempts += 1
                        self._health_score = max(0.0, self._health_score - 5)
                        if self._reconnect_attempts >= self._max_reconnect_attempts:
                            logger.error("heartbeat.max_reconnect_attempts_reached", peer_ip=self.peer_ip)
                            if self.on_connection_lost:
                                await self.on_connection_lost()
                            break
                        await asyncio.sleep(backoff)
                        continue
                    except Exception as e:
                        logger.error("heartbeat.tcp_connect_error", peer_ip=self.peer_ip, error=str(e))
                        self._reconnect_attempts += 1
                        self._health_score = max(0.0, self._health_score - 5)
                        await asyncio.sleep(self.interval)
                        continue
                
                heartbeat_msg = {
                    'type': 'HEARTBEAT',
                    'timestamp': datetime.now().isoformat(),
                    'role': 'WORKER',
                    'health_score': self._health_score,
                    'token': settings.SYNAPSE_SECRET_TOKEN  # Token de autenticación
                }
                
                data = json.dumps(heartbeat_msg).encode('utf-8')
                self._writer.write(data)
                await self._writer.drain()
                logger.debug("heartbeat.sent", health_score=self._health_score)
                
                self._consecutive_failures = 0  # Resetear fallos tras envío exitoso
                await asyncio.sleep(self.interval)
                
            except Exception as e:
                logger.error("heartbeat.send_error", peer_ip=self.peer_ip, error=str(e))
                self._reader = None
                self._writer = None
                self._consecutive_failures += 1
                self._health_score = max(0.0, self._health_score - 10)
                
                if self._consecutive_failures >= self._max_consecutive_failures:
                    logger.warning("heartbeat.consecutive_failures_exceeded", failures=self._consecutive_failures)
                    if self.on_connection_lost:
                        await self.on_connection_lost()
                
                await asyncio.sleep(self.interval)
    
    async def _listen_heartbeats(self):
        """Master escucha heartbeats del Worker via asyncio Server."""
        try:
            self._server = await asyncio.start_server(
                self._handle_client,
                "0.0.0.0",
                54322
            )
            logger.info("heartbeat.listening", port=54322)
            
            # Monitor de timeout en background
            monitor_task = asyncio.create_task(self._monitor_timeout())
            
            async with self._server:
                await self._server.serve_forever()
                
        except asyncio.CancelledError:
            logger.info("heartbeat.cancelled")
        except Exception as e:
            logger.error("heartbeat.listen_error", error=str(e))
    
    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Maneja una conexión de heartbeat entrante (Master) con autenticación."""
        peer_ip = writer.get_extra_info('peername')[0]
        logger.info("heartbeat.client_connected", peer_ip=peer_ip)
        
        # Autenticación inicial - esperar handshake con token
        try:
            initial_data = await asyncio.wait_for(reader.read(4096), timeout=10.0)
            if not initial_data:
                logger.warning("heartbeat.no_initial_data", peer_ip=peer_ip)
                writer.close()
                await writer.wait_closed()
                return
            
            message = json.loads(initial_data.decode('utf-8'))
            
            # Validar token de seguridad
            if message.get('type') == 'HEARTBEAT':
                received_token = message.get('token')
                if received_token and received_token != settings.SYNAPSE_SECRET_TOKEN:
                    logger.warning("heartbeat.auth_failed", peer_ip=peer_ip)
                    writer.close()
                    await writer.wait_closed()
                    return
            else:
                logger.warning("heartbeat.invalid_initial_message", peer_ip=peer_ip)
                writer.close()
                await writer.wait_closed()
                return
                
        except asyncio.TimeoutError:
            logger.warning("heartbeat.auth_timeout", peer_ip=peer_ip)
            writer.close()
            await writer.wait_closed()
            return
        except json.JSONDecodeError:
            logger.warning("heartbeat.invalid_json", peer_ip=peer_ip)
            writer.close()
            await writer.wait_closed()
            return
        
        try:
            while self.running:
                try:
                    data = await asyncio.wait_for(
                        reader.read(1024),
                        timeout=self.timeout + 5
                    )
                    
                    if not data:
                        break
                    
                    try:
                        message = json.loads(data.decode('utf-8'))
                        
                        if message.get('type') == 'HEARTBEAT':
                            self.last_heartbeat = datetime.now()
                            self.peer_ip = peer_ip
                            # Actualizar health score basado en datos del heartbeat
                            health_score = message.get('health_score', 100.0)
                            logger.debug("heartbeat.received", peer_ip=peer_ip, health_score=health_score)
                            
                            if self.on_heartbeat_received:
                                await self.on_heartbeat_received(peer_ip)
                    
                    except json.JSONDecodeError:
                        logger.warning("heartbeat.invalid_message", peer_ip=peer_ip)
                
                except asyncio.TimeoutError:
                    logger.warning("heartbeat.client_timeout", peer_ip=peer_ip)
                    break
                    
        except Exception as e:
            logger.error("heartbeat.client_error", peer_ip=peer_ip, error=str(e))
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
            logger.info("heartbeat.client_disconnected", peer_ip=peer_ip)
    
    async def _monitor_timeout(self):
        """Monitorea timeout de heartbeat y notifica desconexiones con health score."""
        while self.running:
            try:
                await asyncio.sleep(self.interval)
                
                if self.last_heartbeat:
                    elapsed = (datetime.now() - self.last_heartbeat).total_seconds()
                    if elapsed > self.timeout:
                        # Degradar health score gradualmente
                        self._health_score = max(0.0, self._health_score - 15)
                        logger.warning("heartbeat.timeout", elapsed=elapsed, timeout=self.timeout, health_score=self._health_score)
                        if self.on_connection_lost:
                            await self.on_connection_lost()
                    else:
                        # Recuperación gradual si hay heartbeat reciente
                        if self._health_score < 100.0:
                            self._health_score = min(100.0, self._health_score + 2)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("heartbeat.monitor_error", error=str(e))
    
    def get_health_score(self) -> float:
        """Retorna el health score actual de la conexión (0-100)."""
        return self._health_score
    
    def is_alive(self) -> bool:
        """Verifica si el peer está vivo basado en heartbeat y health score."""
        if not self.last_heartbeat:
            return False
        
        elapsed = (datetime.now() - self.last_heartbeat).total_seconds()
        return elapsed < self.timeout and self._health_score > 50.0
    
    def get_last_heartbeat_time(self) -> Optional[datetime]:
        """Retorna el timestamp del último heartbeat."""
        return self.last_heartbeat
    
    def get_peer_ip(self) -> Optional[str]:
        """Retorna la IP del peer."""
        return self.peer_ip

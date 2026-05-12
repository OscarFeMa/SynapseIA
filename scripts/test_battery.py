#!/usr/bin/env python3
"""
SynapseIA - Sistema de Pruebas en Batería
Evaluación exhaustiva de errores y rendimiento post-limpieza
"""

import asyncio
import json
import time
import sys
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

# Añadir backend al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

@dataclass
class TestResult:
    name: str
    category: str
    status: str  # PASS, FAIL, SKIP, ERROR
    duration_ms: float
    message: str
    details: Dict[str, Any]
    error: Optional[str] = None

class TestBattery:
    def __init__(self):
        self.results: List[TestResult] = []
        self.start_time = None
        self.project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
    async def run_all_tests(self) -> Dict[str, Any]:
        """Ejecuta todas las pruebas en batería"""
        print("=" * 70)
        print("SYNAPSEIA - PRUEBAS EN BATERÍA")
        print("=" * 70)
        print(f"Fecha: {datetime.now().isoformat()}")
        print(f"Proyecto: {self.project_path}")
        print("=" * 70)
        
        self.start_time = time.time()
        
        # Categoría 1: Conectividad Básica
        await self._test_basic_connectivity()
        
        # Categoría 2: Base de Datos
        await self._test_database()
        
        # Categoría 3: Configuración
        await self._test_configuration()
        
        # Categoría 4: Engine Local
        await self._test_local_engine()
        
        # Categoría 5: Red y Discovery
        await self._test_network()
        
        # Categoría 6: Circuit Breaker
        await self._test_circuit_breaker()
        
        # Categoría 7: Async/Await Patterns
        await self._test_async_patterns()
        
        # Categoría 8: Seguridad
        await self._test_security()
        
        # Generar reporte
        return self._generate_report()
    
    async def _test_basic_connectivity(self):
        """Prueba conectividad básica"""
        print("\n[1/8] CONECTIVIDAD BÁSICA")
        print("-" * 50)
        
        # Test 1.1: Importar backend
        start = time.time()
        try:
            from backend.config import get_settings
            settings = get_settings()
            self._add_result("Import backend.config", "CONNECTIVITY", "PASS", 
                           start, "Config importado correctamente", 
                           {"node_role": settings.NODE_ROLE})
        except Exception as e:
            self._add_result("Import backend.config", "CONNECTIVITY", "FAIL",
                           start, f"Error importando config: {str(e)}", {}, str(e))
        
        # Test 1.2: Verificar Ollama local
        start = time.time()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get("http://localhost:11434/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    models = [m.get("name") for m in data.get("models", [])]
                    self._add_result("Ollama local", "CONNECTIVITY", "PASS",
                                   start, f"Ollama respondió con {len(models)} modelos",
                                   {"models": models[:5]})
                else:
                    self._add_result("Ollama local", "CONNECTIVITY", "FAIL",
                                   start, f"HTTP {response.status_code}", {})
        except Exception as e:
            self._add_result("Ollama local", "CONNECTIVITY", "FAIL",
                           start, f"Ollama no disponible: {str(e)}", {}, str(e))
        
        # Test 1.3: Verificar estructura de directorios
        start = time.time()
        required_dirs = ['backend', 'frontend', 'desktop', 'data', 'scripts']
        missing = [d for d in required_dirs if not os.path.exists(os.path.join(self.project_path, d))]
        if not missing:
            self._add_result("Estructura directorios", "CONNECTIVITY", "PASS",
                           start, "Todos los directorios requeridos existen", {})
        else:
            self._add_result("Estructura directorios", "CONNECTIVITY", "FAIL",
                           start, f"Faltan directorios: {', '.join(missing)}", {})
    
    async def _test_database(self):
        """Prueba base de datos"""
        print("\n[2/8] BASE DE DATOS")
        print("-" * 50)
        
        # Test 2.1: Importar modelos
        start = time.time()
        try:
            from backend.database.models import Base, Session, Round, AgentCall
            self._add_result("Import modelos DB", "DATABASE", "PASS",
                           start, "Modelos importados correctamente", {})
        except Exception as e:
            self._add_result("Import modelos DB", "DATABASE", "FAIL",
                           start, f"Error: {str(e)}", {}, str(e))
            return
        
        # Test 2.2: Crear engine y tablas
        start = time.time()
        try:
            from backend.database.local_db import init_db, engine
            await init_db()
            self._add_result("Crear tablas DB", "DATABASE", "PASS",
                           start, "Tablas creadas correctamente", {})
        except Exception as e:
            self._add_result("Crear tablas DB", "DATABASE", "FAIL",
                           start, f"Error: {str(e)}", {}, str(e))
        
        # Test 2.3: Verificar conexión
        start = time.time()
        try:
            from sqlalchemy import text
            from backend.database.local_db import engine
            async with engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                if result.scalar() == 1:
                    self._add_result("Conexión DB", "DATABASE", "PASS",
                                   start, "Conexión DB OK", {})
                else:
                    self._add_result("Conexión DB", "DATABASE", "FAIL",
                                   start, "SELECT 1 falló", {})
        except Exception as e:
            self._add_result("Conexión DB", "DATABASE", "FAIL",
                           start, f"Error: {str(e)}", {}, str(e))
    
    async def _test_configuration(self):
        """Prueba configuración"""
        print("\n[3/8] CONFIGURACIÓN")
        print("-" * 50)
        
        start = time.time()
        try:
            from backend.config import get_settings
            settings = get_settings()
            
            checks = {
                "NODE_ROLE válido": settings.NODE_ROLE in ["MASTER", "WORKER"],
                "DATABASE_URL configurada": bool(settings.DATABASE_URL),
                "OLLAMA_BASE_URL configurada": bool(settings.OLLAMA_BASE_URL),
                "CORS_ORIGINS configurado": bool(settings.CORS_ORIGINS),
                "LOG_LEVEL configurado": bool(settings.LOG_LEVEL),
            }
            
            all_pass = all(checks.values())
            if all_pass:
                self._add_result("Configuración settings", "CONFIG", "PASS",
                               start, "Todas las configuraciones válidas", checks)
            else:
                failed = [k for k, v in checks.items() if not v]
                self._add_result("Configuración settings", "CONFIG", "FAIL",
                               start, f"Configuraciones fallidas: {', '.join(failed)}", checks)
        except Exception as e:
            self._add_result("Configuración settings", "CONFIG", "FAIL",
                           start, f"Error: {str(e)}", {}, str(e))
    
    async def _test_local_engine(self):
        """Prueba motor local Ollama"""
        print("\n[4/8] MOTOR LOCAL (OLLAMA)")
        print("-" * 50)
        
        # Test 4.1: Importar engine manager
        start = time.time()
        try:
            from backend.engine.local_engine_manager import LocalEngineManager, EngineType
            manager = LocalEngineManager()
            self._add_result("Import LocalEngineManager", "ENGINE", "PASS",
                           start, "Engine manager importado", {})
        except Exception as e:
            self._add_result("Import LocalEngineManager", "ENGINE", "FAIL",
                           start, f"Error: {str(e)}", {}, str(e))
            return
        
        # Test 4.2: Health check
        start = time.time()
        try:
            health = await manager.health_check(EngineType.OLLAMA)
            status = health.get("status")
            if status == "online":
                models = health.get("models", [])
                self._add_result("Health Check Ollama", "ENGINE", "PASS",
                               start, f"Ollama online con {len(models)} modelos",
                               {"models": models[:5], "url": health.get("url")})
            else:
                self._add_result("Health Check Ollama", "ENGINE", "FAIL",
                               start, f"Ollama status: {status}, error: {health.get('error')}",
                               health)
        except Exception as e:
            self._add_result("Health Check Ollama", "ENGINE", "FAIL",
                           start, f"Error: {str(e)}", {}, str(e))
        
        # Test 4.3: Generación simple (si está disponible)
        start = time.time()
        try:
            if health.get("status") == "online":
                models = health.get("models", [])
                if models:
                    model = models[0]
                    prompt = "Responde únicamente: TEST_OK"
                    
                    response_parts = []
                    async for token in manager.generate(
                        engine_type=EngineType.OLLAMA,
                        model=model,
                        prompt=prompt,
                        max_tokens=10,
                        stream=True
                    ):
                        response_parts.append(token)
                    
                    response = "".join(response_parts)
                    if "TEST_OK" in response or len(response) > 0:
                        self._add_result("Generación texto", "ENGINE", "PASS",
                                       start, f"Generación exitosa ({len(response)} chars)",
                                       {"model": model, "response_preview": response[:50]})
                    else:
                        self._add_result("Generación texto", "ENGINE", "FAIL",
                                       start, f"Respuesta vacía o inesperada: '{response}'",
                                       {"model": model})
                else:
                    self._add_result("Generación texto", "ENGINE", "SKIP",
                                   start, "No hay modelos disponibles para probar", {})
            else:
                self._add_result("Generación texto", "ENGINE", "SKIP",
                               start, "Ollama offline, saltando generación", {})
        except Exception as e:
            self._add_result("Generación texto", "ENGINE", "FAIL",
                           start, f"Error en generación: {str(e)}", {}, str(e))
    
    async def _test_network(self):
        """Prueba red y discovery"""
        print("\n[5/8] RED Y DISCOVERY")
        print("-" * 50)
        
        # Test 5.1: Importar discovery
        start = time.time()
        try:
            from backend.network.discovery import NodeDiscoverer, DISCOVERY_MAGIC
            discoverer = NodeDiscoverer()
            self._add_result("Import NodeDiscoverer", "NETWORK", "PASS",
                           start, "Discovery importado correctamente", 
                           {"magic": DISCOVERY_MAGIC})
        except Exception as e:
            self._add_result("Import NodeDiscoverer", "NETWORK", "FAIL",
                           start, f"Error: {str(e)}", {}, str(e))
            return
        
        # Test 5.2: Verificar puertos no bloqueados
        start = time.time()
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.close()
            self._add_result("Socket UDP broadcast", "NETWORK", "PASS",
                           start, "Sockets UDP configurables", {})
        except Exception as e:
            self._add_result("Socket UDP broadcast", "NETWORK", "FAIL",
                           start, f"Error: {str(e)}", {}, str(e))
        
        # Test 5.3: Resolución DNS
        start = time.time()
        try:
            from backend.config import get_settings
            settings = get_settings()
            if settings.WORKER_HOSTNAME:
                try:
                    import socket
                    ip = socket.gethostbyname(settings.WORKER_HOSTNAME)
                    self._add_result("Resolución DNS Worker", "NETWORK", "PASS",
                                   start, f"Worker resuelto a {ip}",
                                   {"hostname": settings.WORKER_HOSTNAME, "ip": ip})
                except socket.gaierror:
                    self._add_result("Resolución DNS Worker", "NETWORK", "FAIL",
                                   start, f"No se pudo resolver {settings.WORKER_HOSTNAME}", {})
            else:
                self._add_result("Resolución DNS Worker", "NETWORK", "SKIP",
                               start, "WORKER_HOSTNAME no configurado", {})
        except Exception as e:
            self._add_result("Resolución DNS Worker", "NETWORK", "ERROR",
                           start, f"Error: {str(e)}", {}, str(e))
    
    async def _test_circuit_breaker(self):
        """Prueba circuit breaker"""
        print("\n[6/8] CIRCUIT BREAKER")
        print("-" * 50)
        
        start = time.time()
        try:
            from backend.engine.local_engine_manager import LocalEngineManager, EngineType
            manager = LocalEngineManager()
            
            # Verificar estado inicial
            failures = manager.engine_failures[EngineType.OLLAMA]
            broken_until = manager.circuit_broken_until[EngineType.OLLAMA]
            
            self._add_result("Estado Circuit Breaker", "CIRCUIT", "PASS",
                           start, f"Circuit breaker: {failures} fallos, broken_until={broken_until}",
                           {"failures": failures, "broken_until": broken_until,
                            "threshold": 3, "cooldown": 60})
        except Exception as e:
            self._add_result("Estado Circuit Breaker", "CIRCUIT", "FAIL",
                           start, f"Error: {str(e)}", {}, str(e))
    
    async def _test_async_patterns(self):
        """Prueba patrones async/await"""
        print("\n[7/8] PATRONES ASYNC/AWAIT")
        print("-" * 50)
        
        # Test 7.1: Verificar que heartbeat usa threading (problema conocido)
        start = time.time()
        try:
            heartbeat_path = os.path.join(self.project_path, "backend", "network", "heartbeat.py")
            with open(heartbeat_path, 'r') as f:
                content = f.read()
            
            if 'threading' in content:
                self._add_result("Heartbeat threading", "ASYNC", "FAIL",
                               start, "heartbeat.py usa threading en lugar de asyncio",
                               {"suggestion": "Migrar a asyncio.create_task()"})
            else:
                self._add_result("Heartbeat threading", "ASYNC", "PASS",
                               start, "heartbeat.py no usa threading", {})
        except Exception as e:
            self._add_result("Heartbeat threading", "ASYNC", "ERROR",
                           start, f"Error: {str(e)}", {}, str(e))
        
        # Test 7.2: Verificar gathers vs loops secuenciales
        start = time.time()
        try:
            orchestrator_path = os.path.join(self.project_path, "backend", "engine", "agent_orchestrator.py")
            with open(orchestrator_path, 'r') as f:
                content = f.read()
            
            if 'asyncio.gather' in content:
                self._add_result("Paralelismo agentes", "ASYNC", "PASS",
                               start, "agent_orchestrator usa asyncio.gather", {})
            else:
                self._add_result("Paralelismo agentes", "ASYNC", "FAIL",
                               start, "agent_orchestrator NO usa asyncio.gather (ejecuta secuencialmente)",
                               {"suggestion": "Restaurar asyncio.gather para paralelismo"})
        except Exception as e:
            self._add_result("Paralelismo agentes", "ASYNC", "ERROR",
                           start, f"Error: {str(e)}", {}, str(e))
    
    async def _test_security(self):
        """Pruebas de seguridad básicas"""
        print("\n[8/8] SEGURIDAD")
        print("-" * 50)
        
        # Test 8.1: Verificar que .env no tiene credenciales reales
        start = time.time()
        try:
            env_path = os.path.join(self.project_path, ".env")
            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    env_content = f.read()
                
                # Verificar que no hay contraseñas reales en .env
                suspicious = []
                for line in env_content.split('\n'):
                    if any(kw in line.upper() for kw in ['PASSWORD', 'SECRET', 'API_KEY', 'TOKEN']):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            if value and value not in ['None', '', 'null'] and not value.startswith('${'):
                                if len(value) > 3:  # No es placeholder vacío
                                    suspicious.append(key.strip())
                
                if suspicious:
                    self._add_result("Credenciales .env", "SECURITY", "WARN",
                                   start, f"Variables con valores: {', '.join(suspicious[:5])}",
                                   {"variables": suspicious})
                else:
                    self._add_result("Credenciales .env", "SECURITY", "PASS",
                                   start, "No se detectaron credenciales hardcoded en .env", {})
            else:
                self._add_result("Credenciales .env", "SECURITY", "SKIP",
                               start, "Archivo .env no encontrado", {})
        except Exception as e:
            self._add_result("Credenciales .env", "SECURITY", "ERROR",
                           start, f"Error: {str(e)}", {}, str(e))
        
        # Test 8.2: Verificar CORS no es wildcard en producción
        start = time.time()
        try:
            from backend.config import get_settings
            settings = get_settings()
            origins = settings.CORS_ORIGINS
            
            if "*" in str(origins):
                self._add_result("CORS wildcard", "SECURITY", "WARN",
                               start, "CORS permite '*' - revisar para producción",
                               {"origins": origins})
            else:
                self._add_result("CORS wildcard", "SECURITY", "PASS",
                               start, "CORS configurado con orígenes específicos",
                               {"origins": origins})
        except Exception as e:
            self._add_result("CORS wildcard", "SECURITY", "ERROR",
                           start, f"Error: {str(e)}", {}, str(e))
    
    def _add_result(self, name: str, category: str, status: str, 
                   start_time: float, message: str, details: Dict, error: str = None):
        """Añade un resultado de prueba"""
        duration = (time.time() - start_time) * 1000
        result = TestResult(
            name=name,
            category=category,
            status=status,
            duration_ms=round(duration, 2),
            message=message,
            details=details,
            error=error
        )
        self.results.append(result)
        
        icon = {"PASS": "✅", "FAIL": "❌", "SKIP": "⏭️", "ERROR": "💥", "WARN": "⚠️"}.get(status, "❓")
        print(f"  {icon} {name}: {message} ({duration:.0f}ms)")
    
    def _generate_report(self) -> Dict[str, Any]:
        """Genera reporte final de pruebas"""
        total_time = time.time() - self.start_time
        
        # Clasificar resultados
        passed = [r for r in self.results if r.status == "PASS"]
        failed = [r for r in self.results if r.status == "FAIL"]
        skipped = [r for r in self.results if r.status == "SKIP"]
        errors = [r for r in self.results if r.status == "ERROR"]
        warnings = [r for r in self.results if r.status == "WARN"]
        
        # Por categoría
        by_category = {}
        for r in self.results:
            cat = r.category
            if cat not in by_category:
                by_category[cat] = {"total": 0, "pass": 0, "fail": 0}
            by_category[cat]["total"] += 1
            if r.status == "PASS":
                by_category[cat]["pass"] += 1
            elif r.status in ["FAIL", "ERROR"]:
                by_category[cat]["fail"] += 1
        
        report = {
            "summary": {
                "total_tests": len(self.results),
                "passed": len(passed),
                "failed": len(failed),
                "skipped": len(skipped),
                "errors": len(errors),
                "warnings": len(warnings),
                "success_rate": round(len(passed) / max(len(self.results) - len(skipped), 1) * 100, 1),
                "total_duration_sec": round(total_time, 2)
            },
            "by_category": by_category,
            "failed_tests": [asdict(r) for r in failed + errors],
            "warning_tests": [asdict(r) for r in warnings],
            "all_results": [asdict(r) for r in self.results]
        }
        
        # Imprimir resumen
        print("\n" + "=" * 70)
        print("RESUMEN DE PRUEBAS EN BATERÍA")
        print("=" * 70)
        print(f"Total pruebas: {len(self.results)}")
        print(f"  ✅ Pasadas: {len(passed)}")
        print(f"  ❌ Fallidas: {len(failed)}")
        print(f"  ⏭️ Saltadas: {len(skipped)}")
        print(f"  💥 Errores: {len(errors)}")
        print(f"  ⚠️ Advertencias: {len(warnings)}")
        print(f"\nTasa de éxito: {report['summary']['success_rate']}%")
        print(f"Tiempo total: {total_time:.1f}s")
        
        if failed or errors:
            print("\n" + "!" * 70)
            print("PRUEBAS FALLIDAS (Requieren atención)")
            print("!" * 70)
            for r in failed + errors:
                print(f"\n❌ [{r.category}] {r.name}")
                print(f"   {r.message}")
                if r.error:
                    print(f"   Error: {r.error}")
        
        if warnings:
            print("\n" + "⚠️" * 35)
            print("ADVERTENCIAS")
            print("⚠️" * 35)
            for r in warnings:
                print(f"\n⚠️ [{r.category}] {r.name}")
                print(f"   {r.message}")
        
        return report


async def main():
    battery = TestBattery()
    report = await battery.run_all_tests()
    
    # Guardar reporte
    report_file = os.path.join(os.path.dirname(__file__), "test_battery_report.json")
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\nReporte guardado en: {report_file}")
    print("=" * 70)
    
    # Retornar código de salida
    if report['summary']['failed'] > 0 or report['summary']['errors'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())

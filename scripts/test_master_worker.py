#!/usr/bin/env python3
"""
SynapseIA - Prueba Integral Master/Worker
Verifica que las correcciones críticas funcionan con Worker activo.
"""

import asyncio
import sys
import os
import time
import json
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class MasterWorkerTest:
    def __init__(self):
        self.results = []
        
    async def run_tests(self):
        print("=" * 70)
        print("SYNAPSEIA - PRUEBA INTEGRAL MASTER/WORKER")
        print("=" * 70)
        print(f"Fecha: {datetime.now().isoformat()}")
        print("Asegúrate de que el Worker está ENCENDIDO antes de continuar.")
        print("=" * 70)
        
        # 1. Verificar descubrimiento de red
        await self._test_discovery()
        
        # 2. Verificar heartbeat
        await self._test_heartbeat()
        
        # 3. Verificar generación vía Worker
        await self._test_worker_generation()
        
        # 4. Verificar circuit breaker con Worker
        await self._test_circuit_worker()
        
        # Reporte final
        self._print_report()
    
    async def _test_discovery(self):
        print("\n[1/4] DESCUBRIMIENTO DE RED")
        print("-" * 50)
        
        try:
            from backend.network.discovery import NodeDiscoverer
            from backend.config import get_settings
            
            settings = get_settings()
            discoverer = NodeDiscoverer()
            
            # Iniciar discovery brevemente
            await discoverer.start()
            await asyncio.sleep(3)  # Esperar beacons
            
            peers = discoverer.get_active_peers()
            workers = [p for p in peers if p.get("role") == "WORKER"]
            
            await discoverer.stop()
            
            if workers:
                worker_ip = workers[0]["ip"]
                settings.update_worker_host(worker_ip)
                print(f"  ✅ Worker descubierto: {worker_ip}")
                self.results.append({"test": "Discovery", "status": "PASS", "worker_ip": worker_ip})
            else:
                # Fallback: usar hostname
                resolved = settings.resolve_worker_ip()
                if resolved:
                    settings.update_worker_host(resolved)
                    print(f"  ⚠️  Worker descubierto via DNS: {resolved}")
                    self.results.append({"test": "Discovery", "status": "WARN", "worker_ip": resolved, "note": "via DNS, no UDP beacon"})
                else:
                    print(f"  ❌ Worker no encontrado")
                    self.results.append({"test": "Discovery", "status": "FAIL", "error": "No se detectó Worker"})
        
        except Exception as e:
            print(f"  ❌ Error: {e}")
            self.results.append({"test": "Discovery", "status": "ERROR", "error": str(e)})
    
    async def _test_heartbeat(self):
        print("\n[2/4] HEARTBEAT ASYNC")
        print("-" * 50)
        
        try:
            from backend.network.heartbeat import HeartbeatManager
            from backend.config import get_settings
            
            settings = get_settings()
            worker_ip = settings.get_worker_host()
            
            if not worker_ip:
                print("  ⏭️  Saltando heartbeat (Worker no encontrado)")
                self.results.append({"test": "Heartbeat", "status": "SKIP"})
                return
            
            # Probar como Master (escuchar)
            hb = HeartbeatManager(role="MASTER", interval=2, timeout=5)
            
            heartbeat_received = asyncio.Event()
            
            async def on_heartbeat(ip):
                print(f"  ✅ Heartbeat recibido de {ip}")
                heartbeat_received.set()
            
            hb.on_heartbeat_received = on_heartbeat
            
            await hb.start()
            
            # Esperar heartbeat del Worker (máximo 10s)
            try:
                await asyncio.wait_for(heartbeat_received.wait(), timeout=10.0)
                self.results.append({"test": "Heartbeat", "status": "PASS", "worker_ip": worker_ip})
            except asyncio.TimeoutError:
                print(f"  ⚠️  Timeout esperando heartbeat (Worker puede no estar enviando)")
                self.results.append({"test": "Heartbeat", "status": "WARN", "note": "Worker no envió heartbeat en 10s"})
            
            await hb.stop()
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            self.results.append({"test": "Heartbeat", "status": "ERROR", "error": str(e)})
    
    async def _test_worker_generation(self):
        print("\n[3/4] GENERACIÓN VÍA WORKER")
        print("-" * 50)
        
        try:
            from backend.engine.local_engine_manager import LocalEngineManager, EngineType
            from backend.config import get_settings
            
            settings = get_settings()
            manager = LocalEngineManager()
            
            # Verificar que apunta al Worker
            print(f"  URL Worker Ollama: {settings.worker_ollama_url}")
            
            # Health check
            health = await manager.health_check(EngineType.OLLAMA)
            if health.get("status") != "online":
                print(f"  ❌ Worker Ollama offline: {health.get('error')}")
                self.results.append({"test": "Worker Generation", "status": "FAIL", "error": health.get("error")})
                return
            
            print(f"  ✅ Worker Ollama online")
            
            # Generación simple con timeout de 30s
            models = health.get("models", [])
            if not models:
                print("  ⏭️  No hay modelos disponibles")
                self.results.append({"test": "Worker Generation", "status": "SKIP"})
                return
            
            model = models[0]
            print(f"  Probando modelo: {model}")
            
            response_parts = []
            start = time.time()
            
            try:
                # Crear generador con timeout
                async def generate_with_timeout():
                    async for token in manager.generate(
                        engine_type=EngineType.OLLAMA,
                        model=model,
                        prompt="Responde únicamente: OK",
                        max_tokens=5,
                        stream=True
                    ):
                        response_parts.append(token)
                
                await asyncio.wait_for(generate_with_timeout(), timeout=30.0)
                
                response = "".join(response_parts)
                elapsed = time.time() - start
                
                if response:
                    print(f"  ✅ Generación exitosa ({len(response)} chars, {elapsed:.1f}s)")
                    self.results.append({"test": "Worker Generation", "status": "PASS", "model": model, "response": response[:50], "duration": elapsed})
                else:
                    print(f"  ❌ Respuesta vacía")
                    self.results.append({"test": "Worker Generation", "status": "FAIL", "error": "Respuesta vacía"})
            
            except asyncio.TimeoutError:
                print(f"  ❌ Timeout en generación (30s)")
                self.results.append({"test": "Worker Generation", "status": "FAIL", "error": "Timeout 30s"})
        
        except Exception as e:
            print(f"  ❌ Error: {e}")
            self.results.append({"test": "Worker Generation", "status": "ERROR", "error": str(e)})
    
    async def _test_circuit_worker(self):
        print("\n[4/4] CIRCUIT BREAKER CON WORKER")
        print("-" * 50)
        
        try:
            from backend.engine.local_engine_manager import LocalEngineManager, EngineType
            
            manager = LocalEngineManager()
            
            failures = manager.engine_failures[EngineType.OLLAMA]
            broken = manager.circuit_broken_until[EngineType.OLLAMA]
            
            print(f"  Fallos: {failures}/10, Circuit broken: {broken}")
            
            if failures == 0 and broken == 0:
                print(f"  ✅ Circuit breaker en estado normal")
                self.results.append({"test": "Circuit Worker", "status": "PASS", "failures": failures, "broken": broken})
            else:
                print(f"  ⚠️  Circuit breaker con estado activo")
                self.results.append({"test": "Circuit Worker", "status": "WARN", "failures": failures, "broken": broken})
        
        except Exception as e:
            print(f"  ❌ Error: {e}")
            self.results.append({"test": "Circuit Worker", "status": "ERROR", "error": str(e)})
    
    def _print_report(self):
        print("\n" + "=" * 70)
        print("RESUMEN DE PRUEBA MASTER/WORKER")
        print("=" * 70)
        
        passed = [r for r in self.results if r["status"] == "PASS"]
        failed = [r for r in self.results if r["status"] in ["FAIL", "ERROR"]]
        warns = [r for r in self.results if r["status"] == "WARN"]
        skipped = [r for r in self.results if r["status"] == "SKIP"]
        
        print(f"  ✅ Pasadas: {len(passed)}")
        print(f"  ❌ Fallidas: {len(failed)}")
        print(f"  ⚠️  Advertencias: {len(warns)}")
        print(f"  ⏭️  Saltadas: {len(skipped)}")
        
        if failed:
            print("\n❌ PRUEBAS FALLIDAS:")
            for r in failed:
                print(f"   - {r['test']}: {r.get('error', 'Unknown')}")
        
        if warns:
            print("\n⚠️  ADVERTENCIAS:")
            for r in warns:
                print(f"   - {r['test']}: {r.get('note', 'Revisar')}")
        
        # Guardar reporte
        report_file = os.path.join(os.path.dirname(__file__), "test_master_worker_report.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({"results": self.results, "timestamp": datetime.now().isoformat()}, f, indent=2)
        
        print(f"\nReporte guardado en: {report_file}")
        print("=" * 70)


async def main():
    test = MasterWorkerTest()
    await test.run_tests()


if __name__ == "__main__":
    asyncio.run(main())

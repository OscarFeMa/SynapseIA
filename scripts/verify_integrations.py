#!/usr/bin/env python3
"""
SynapseIA - Verificación de Integraciones
Script de diagnóstico para verificar todas las conexiones.
"""
import asyncio
import sys
import os
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class IntegrationVerifier:
    """Verifica el estado de todas las integraciones."""
    
    def __init__(self):
        self.results = {}
        
    async def run_all_checks(self):
        print("=" * 70)
        print("SYNAPSEIA - VERIFICACIÓN DE INTEGRACIONES")
        print("=" * 70)
        
        # 1. SQLite Local
        await self._check_sqlite()
        
        # 2. Configuración
        await self._check_config()
        
        # 3. Docker
        await self._check_docker()
        
        # 4. Frontend
        await self._check_frontend()
        
        # 5. Tests
        await self._check_tests()
        
        # 6. Redis (si está configurado)
        await self._check_redis()
        
        # 7. Supabase (si está configurado)
        await self._check_supabase()
        
        # Reporte final
        self._print_report()
    
    async def _check_sqlite(self):
        print("\n[1/7] SQLite Local")
        print("-" * 50)
        try:
            from backend.database.local_db import engine, init_db
            from sqlalchemy import text
            
            async with engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                if result.scalar() == 1:
                    print("  ✅ SQLite: Conexión OK")
                    self.results['sqlite'] = {'status': 'OK', 'message': 'Conexión funcional'}
                else:
                    print("  ❌ SQLite: SELECT 1 falló")
                    self.results['sqlite'] = {'status': 'ERROR', 'message': 'SELECT 1 falló'}
        except Exception as e:
            print(f"  ❌ SQLite: {e}")
            self.results['sqlite'] = {'status': 'ERROR', 'message': str(e)}
    
    async def _check_config(self):
        print("\n[2/7] Configuración")
        print("-" * 50)
        try:
            from backend.config import get_settings
            settings = get_settings()
            
            checks = {
                'NODE_ROLE': settings.NODE_ROLE,
                'DATABASE_URL': settings.DATABASE_URL[:30] + "..." if len(settings.DATABASE_URL) > 30 else settings.DATABASE_URL,
                'OLLAMA_BASE_URL': settings.OLLAMA_BASE_URL,
                'SYNAPSE_SECRET_TOKEN': settings.SYNAPSE_SECRET_TOKEN[:10] + "...",
            }
            
            print("  ✅ Configuración cargada:")
            for key, value in checks.items():
                print(f"     {key}: {value}")
            
            self.results['config'] = {'status': 'OK', 'message': 'Configuración cargada', 'checks': checks}
        except Exception as e:
            print(f"  ❌ Configuración: {e}")
            self.results['config'] = {'status': 'ERROR', 'message': str(e)}
    
    async def _check_docker(self):
        print("\n[3/7] Docker")
        print("-" * 50)
        try:
            docker_compose = Path(__file__).parent.parent / "docker-compose.yml"
            dockerfile_master = Path(__file__).parent.parent / "Dockerfile.master"
            dockerfile_worker = Path(__file__).parent.parent / "Dockerfile.worker"
            
            all_exist = all([
                docker_compose.exists(),
                dockerfile_master.exists(),
                dockerfile_worker.exists()
            ])
            
            if all_exist:
                print("  ✅ Docker: Archivos configuración presentes")
                print(f"     - docker-compose.yml: {docker_compose.exists()}")
                print(f"     - Dockerfile.master: {dockerfile_master.exists()}")
                print(f"     - Dockerfile.worker: {dockerfile_worker.exists()}")
                self.results['docker'] = {'status': 'OK', 'message': 'Configuración completa'}
            else:
                print("  ⚠️ Docker: Faltan archivos")
                self.results['docker'] = {'status': 'WARN', 'message': 'Faltan archivos'}
        except Exception as e:
            print(f"  ❌ Docker: {e}")
            self.results['docker'] = {'status': 'ERROR', 'message': str(e)}
    
    async def _check_frontend(self):
        print("\n[4/7] Frontend")
        print("-" * 50)
        try:
            frontend_dir = Path(__file__).parent.parent / "frontend"
            web_interface = Path(__file__).parent.parent / "web_interface"
            
            index_html = frontend_dir / "index.html"
            debate_manager = web_interface / "debate_manager.html"
            
            if index_html.exists() and debate_manager.exists():
                print("  ✅ Frontend: Archivos presentes")
                print(f"     - index.html: {index_html.stat().st_size} bytes")
                print(f"     - debate_manager.html: {debate_manager.stat().st_size} bytes")
                self.results['frontend'] = {'status': 'OK', 'message': 'Frontend presente'}
            else:
                print("  ⚠️ Frontend: Algunos archivos faltan")
                self.results['frontend'] = {'status': 'WARN', 'message': 'Archivos incompletos'}
        except Exception as e:
            print(f"  ❌ Frontend: {e}")
            self.results['frontend'] = {'status': 'ERROR', 'message': str(e)}
    
    async def _check_tests(self):
        print("\n[5/7] Tests")
        print("-" * 50)
        try:
            scripts_dir = Path(__file__).parent.parent / "scripts"
            test_files = list(scripts_dir.glob("test*.py"))
            
            print(f"  ✅ Tests: {len(test_files)} archivos encontrados")
            for test_file in test_files[:5]:
                print(f"     - {test_file.name}")
            
            self.results['tests'] = {'status': 'OK', 'message': f'{len(test_files)} tests encontrados', 'count': len(test_files)}
        except Exception as e:
            print(f"  ❌ Tests: {e}")
            self.results['tests'] = {'status': 'ERROR', 'message': str(e)}
    
    async def _check_redis(self):
        print("\n[6/7] Redis")
        print("-" * 50)
        try:
            docker_compose = Path(__file__).parent.parent / "docker-compose.yml"
            with open(docker_compose) as f:
                content = f.read()
                if 'redis:' in content:
                    print("  ✅ Redis: Configurado en docker-compose.yml")
                    self.results['redis'] = {'status': 'OK', 'message': 'Configurado en docker-compose'}
                else:
                    print("  ⚠️ Redis: No configurado")
                    self.results['redis'] = {'status': 'WARN', 'message': 'No configurado'}
        except Exception as e:
            print(f"  ❌ Redis: {e}")
            self.results['redis'] = {'status': 'ERROR', 'message': str(e)}
    
    async def _check_supabase(self):
        print("\n[7/7] Supabase")
        print("-" * 50)
        try:
            supabase_setup = Path(__file__).parent.parent / "SUPABASE_SETUP.md"
            supabase_schema = Path(__file__).parent.parent / "supabase_schema.sql"
            
            if supabase_setup.exists() and supabase_schema.exists():
                print("  ✅ Supabase: Documentación y esquema presentes")
                print(f"     - SUPABASE_SETUP.md: {supabase_setup.stat().st_size} bytes")
                print(f"     - supabase_schema.sql: {supabase_schema.stat().st_size} bytes")
                print("  ⚠️ Nota: Integración de código pendiente (solo documentación)")
                self.results['supabase'] = {'status': 'WARN', 'message': 'Documentación presente, código pendiente'}
            else:
                print("  ⚠️ Supabase: Faltan archivos")
                self.results['supabase'] = {'status': 'WARN', 'message': 'Faltan archivos'}
        except Exception as e:
            print(f"  ❌ Supabase: {e}")
            self.results['supabase'] = {'status': 'ERROR', 'message': str(e)}
    
    def _print_report(self):
        print("\n" + "=" * 70)
        print("RESUMEN DE INTEGRACIONES")
        print("=" * 70)
        
        ok = [k for k, v in self.results.items() if v['status'] == 'OK']
        warn = [k for k, v in self.results.items() if v['status'] == 'WARN']
        error = [k for k, v in self.results.items() if v['status'] == 'ERROR']
        
        print(f"  ✅ OK: {len(ok)} - {', '.join(ok)}")
        print(f"  ⚠️  WARN: {len(warn)} - {', '.join(warn)}")
        print(f"  ❌ ERROR: {len(error)} - {', '.join(error)}")
        
        # Guardar reporte
        report_file = Path(__file__).parent / "integration_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\nReporte guardado en: {report_file}")
        print("=" * 70)


async def main():
    verifier = IntegrationVerifier()
    await verifier.run_all_checks()


if __name__ == "__main__":
    asyncio.run(main())

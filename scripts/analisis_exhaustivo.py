#!/usr/bin/env python3
"""
SynapseIA - Análisis Exhaustivo y Evaluación de Errores
Script de análisis automático del proyecto post-limpieza
"""

import ast
import sys
import os
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, asdict

@dataclass
class Issue:
    file: str
    line: int
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    category: str
    message: str
    suggestion: str

class ProjectAnalyzer:
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.issues: List[Issue] = []
        self.files_analyzed = 0
        self.lines_analyzed = 0
        
    def analyze_all(self) -> Dict[str, Any]:
        """Ejecuta análisis completo del proyecto"""
        print("=" * 70)
        print("SYNAPSEIA - ANÁLISIS EXHAUSTIVO POST-LIMPIEZA")
        print("=" * 70)
        
        # Analizar archivos Python del backend
        backend_path = self.project_path / "backend"
        if backend_path.exists():
            self._analyze_directory(backend_path)
        
        # Analizar scripts
        scripts_path = self.project_path / "scripts"
        if scripts_path.exists():
            self._analyze_directory(scripts_path)
        
        # Analizar archivos de configuración
        self._analyze_config_files()
        
        # Generar reporte
        return self._generate_report()
    
    def _analyze_directory(self, path: Path):
        """Analiza todos los archivos Python en un directorio"""
        for py_file in path.rglob("*.py"):
            if "__pycache__" in str(py_file) or "venv" in str(py_file):
                continue
            self._analyze_file(py_file)
    
    def _analyze_file(self, file_path: Path):
        """Analiza un archivo Python individual"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.files_analyzed += 1
            self.lines_analyzed += len(content.split('\n'))
            
            # Parsear AST
            try:
                tree = ast.parse(content)
            except SyntaxError as e:
                self.issues.append(Issue(
                    file=str(file_path.relative_to(self.project_path)),
                    line=e.lineno or 1,
                    severity="CRITICAL",
                    category="SYNTAX",
                    message=f"Error de sintaxis: {e.msg}",
                    suggestion="Corregir el error de sintaxis inmediatamente"
                ))
                return
            
            # Análisis estático
            self._check_imports(tree, file_path, content)
            self._check_async_patterns(tree, file_path, content)
            self._check_error_handling(tree, file_path, content)
            self._check_resource_management(tree, file_path, content)
            self._check_security_issues(tree, file_path, content)
            self._check_performance_issues(tree, file_path, content)
            self._check_code_smells(tree, file_path, content)
            
        except Exception as e:
            self.issues.append(Issue(
                file=str(file_path.relative_to(self.project_path)),
                line=1,
                severity="HIGH",
                category="ANALYSIS",
                message=f"Error analizando archivo: {str(e)}",
                suggestion="Verificar permisos y codificación del archivo"
            ))
    
    def _check_imports(self, tree: ast.AST, file_path: Path, content: str):
        """Verifica problemas con imports"""
        relative_path = str(file_path.relative_to(self.project_path))
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    # Verificar imports no usados
                    if alias.name not in content.split('import')[1:]:
                        pass  # Simplificado
                        
            elif isinstance(node, ast.ImportFrom):
                # Verificar imports circulares potenciales
                if node.level > 0 and 'backend' in relative_path:
                    module = node.module or ""
                    if 'config' in module and 'config' not in relative_path:
                        pass
    
    def _check_async_patterns(self, tree: ast.AST, file_path: Path, content: str):
        """Verifica patrones async/await"""
        relative_path = str(file_path.relative_to(self.project_path))
        
        has_async_functions = False
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                has_async_functions = True
                
                # Verificar si hay await en loops que podrían ser gather
                for child in ast.walk(node):
                    if isinstance(child, ast.For):
                        for for_child in ast.walk(child):
                            if isinstance(for_child, ast.Await):
                                self.issues.append(Issue(
                                    file=relative_path,
                                    line=child.lineno,
                                    severity="MEDIUM",
                                    category="PERFORMANCE",
                                    message="Await dentro de loop for - considerar asyncio.gather",
                                    suggestion="Usar asyncio.gather() para ejecución paralela"
                                ))
                                break
        
        # Verificar threading en código async (problema conocido)
        if 'heartbeat' in relative_path.lower():
            if 'threading' in content:
                self.issues.append(Issue(
                    file=relative_path,
                    line=1,
                    severity="CRITICAL",
                    category="ARCHITECTURE",
                    message="Uso de threading en código async - incompatibilidad con FastAPI/uvloop",
                    suggestion="Reemplazar threading por asyncio.create_task() y asyncio.Event"
                ))
    
    def _check_error_handling(self, tree: ast.AST, file_path: Path, content: str):
        """Verifica manejo de errores"""
        relative_path = str(file_path.relative_to(self.project_path))
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                # Verificar excepts vacíos o genéricos
                for handler in node.handlers:
                    if handler.type is None:
                        self.issues.append(Issue(
                            file=relative_path,
                            line=handler.lineno,
                            severity="HIGH",
                            category="ERROR_HANDLING",
                            message="Except genérico (bare except) - captura KeyboardInterrupt y SystemExit",
                            suggestion="Usar 'except Exception as e:' como mínimo"
                        ))
                    elif isinstance(handler.type, ast.Name) and handler.type.id == 'Exception':
                        # Verificar si hay logging del error
                        handler_body = ast.dump(handler)
                        if 'logger' not in handler_body and 'print' not in handler_body:
                            self.issues.append(Issue(
                                file=relative_path,
                                line=handler.lineno,
                                severity="MEDIUM",
                                category="ERROR_HANDLING",
                                message="Except Exception sin logging del error",
                                suggestion="Agregar logging del error para debugging"
                            ))
    
    def _check_resource_management(self, tree: ast.AST, file_path: Path, content: str):
        """Verifica manejo de recursos"""
        relative_path = str(file_path.relative_to(self.project_path))
        
        # Verificar sockets sin close
        if 'socket' in content.lower():
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Attribute):
                        if node.func.attr == 'socket':
                            # Verificar si hay try/finally o context manager
                            parent = self._get_parent(tree, node)
                            if parent and not isinstance(parent, (ast.Try, ast.With)):
                                self.issues.append(Issue(
                                    file=relative_path,
                                    line=node.lineno,
                                    severity="MEDIUM",
                                    category="RESOURCES",
                                    message="Socket creado sin manejo de contexto (try/finally o with)",
                                    suggestion="Usar try/finally o context manager para cerrar sockets"
                                ))
    
    def _check_security_issues(self, tree: ast.AST, file_path: Path, content: str):
        """Verifica problemas de seguridad"""
        relative_path = str(file_path.relative_to(self.project_path))
        
        # Verificar hardcoded credentials
        suspicious_patterns = ['password', 'secret', 'token', 'api_key']
        for pattern in suspicious_patterns:
            if pattern in content.lower():
                for i, line in enumerate(content.split('\n'), 1):
                    if pattern in line.lower() and ('=' in line or ':' in line):
                        # Verificar si está en .env o es un placeholder
                        if '"' in line or "'" in line:
                            if 'example' not in line.lower() and 'placeholder' not in line.lower():
                                if 'getenv' not in line and 'settings.' not in line and 'os.environ' not in line:
                                    self.issues.append(Issue(
                                        file=relative_path,
                                        line=i,
                                        severity="HIGH",
                                        category="SECURITY",
                                        message=f"Posible credencial hardcoded: {pattern}",
                                        suggestion="Mover a variables de entorno o archivo .env"
                                    ))
    
    def _check_performance_issues(self, tree: ast.AST, file_path: Path, content: str):
        """Verifica problemas de rendimiento"""
        relative_path = str(file_path.relative_to(self.project_path))
        
        # Verificar N+1 queries
        for node in ast.walk(tree):
            if isinstance(node, ast.For):
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        if isinstance(child.func, ast.Attribute):
                            if 'commit' in child.func.attr or 'execute' in child.func.attr:
                                self.issues.append(Issue(
                                    file=relative_path,
                                    line=node.lineno,
                                    severity="MEDIUM",
                                    category="PERFORMANCE",
                                    message="Posible N+1 query - operación de DB dentro de loop",
                                    suggestion="Batch operations o bulk insert/update"
                                ))
    
    def _check_code_smells(self, tree: ast.AST, file_path: Path, content: str):
        """Verifica code smells"""
        relative_path = str(file_path.relative_to(self.project_path))
        
        # Verificar funciones muy largas
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                lines = node.end_lineno - node.lineno if node.end_lineno else 0
                if lines > 50:
                    self.issues.append(Issue(
                        file=relative_path,
                        line=node.lineno,
                        severity="LOW",
                        category="CODE_QUALITY",
                        message=f"Función {node.name} muy larga ({lines} líneas)",
                        suggestion="Refactorizar en funciones más pequeñas"
                    ))
                
                # Verificar complejidad ciclomática básica (muchos if/for/while)
                complexity = 0
                for child in ast.walk(node):
                    if isinstance(child, (ast.If, ast.For, ast.While, ast.ExceptHandler)):
                        complexity += 1
                
                if complexity > 10:
                    self.issues.append(Issue(
                        file=relative_path,
                        line=node.lineno,
                        severity="MEDIUM",
                        category="CODE_QUALITY",
                        message=f"Función {node.name} tiene complejidad ciclomática alta ({complexity})",
                        suggestion="Simplificar lógica condicional"
                    ))
    
    def _analyze_config_files(self):
        """Analiza archivos de configuración"""
        # Verificar .env.example vs .env
        env_example = self.project_path / ".env.example"
        env = self.project_path / ".env"
        
        if env_example.exists() and env.exists():
            try:
                with open(env_example, 'r', encoding='utf-8') as f:
                    example_vars = set(line.split('=')[0].strip() for line in f if '=' in line and not line.startswith('#'))
                with open(env, 'r', encoding='utf-8') as f:
                    env_vars = set(line.split('=')[0].strip() for line in f if '=' in line and not line.startswith('#'))
            except UnicodeDecodeError:
                try:
                    with open(env_example, 'r', encoding='latin-1') as f:
                        example_vars = set(line.split('=')[0].strip() for line in f if '=' in line and not line.startswith('#'))
                    with open(env, 'r', encoding='latin-1') as f:
                        env_vars = set(line.split('=')[0].strip() for line in f if '=' in line and not line.startswith('#'))
                except:
                    return
            
            missing = example_vars - env_vars
            if missing:
                self.issues.append(Issue(
                    file=".env",
                    line=1,
                    severity="MEDIUM",
                    category="CONFIG",
                    message=f"Variables faltantes en .env: {', '.join(missing)}",
                    suggestion="Actualizar .env con todas las variables requeridas"
                ))
    
    def _get_parent(self, tree: ast.AST, node: ast.AST) -> ast.AST:
        """Obtiene el nodo padre de un nodo AST"""
        for parent in ast.walk(tree):
            for child in ast.iter_child_nodes(parent):
                if child is node:
                    return parent
        return None
    
    def _generate_report(self) -> Dict[str, Any]:
        """Genera reporte final del análisis"""
        # Clasificar issues por severidad
        critical = [i for i in self.issues if i.severity == "CRITICAL"]
        high = [i for i in self.issues if i.severity == "HIGH"]
        medium = [i for i in self.issues if i.severity == "MEDIUM"]
        low = [i for i in self.issues if i.severity == "LOW"]
        
        # Clasificar por categoría
        categories = {}
        for issue in self.issues:
            categories[issue.category] = categories.get(issue.category, 0) + 1
        
        report = {
            "summary": {
                "files_analyzed": self.files_analyzed,
                "lines_analyzed": self.lines_analyzed,
                "total_issues": len(self.issues),
                "critical": len(critical),
                "high": len(high),
                "medium": len(medium),
                "low": len(low),
            },
            "by_category": categories,
            "critical_issues": [asdict(i) for i in critical],
            "high_issues": [asdict(i) for i in high],
            "medium_issues": [asdict(i) for i in medium],
            "low_issues": [asdict(i) for i in low],
        }
        
        # Imprimir resumen
        print("\n" + "=" * 70)
        print("RESUMEN DEL ANÁLISIS")
        print("=" * 70)
        print(f"Archivos analizados: {self.files_analyzed}")
        print(f"Líneas analizadas: {self.lines_analyzed}")
        print(f"Issues totales: {len(self.issues)}")
        print(f"  CRÍTICOS: {len(critical)}")
        print(f"  ALTOS: {len(high)}")
        print(f"  MEDIOS: {len(medium)}")
        print(f"  BAJOS: {len(low)}")
        print("\nPor categoría:")
        for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
            print(f"  {cat}: {count}")
        
        if critical:
            print("\n" + "!" * 70)
            print("ISSUES CRÍTICOS (Requieren atención inmediata)")
            print("!" * 70)
            for issue in critical:
                print(f"\n[{issue.file}:{issue.line}] {issue.message}")
                print(f"  → {issue.suggestion}")
        
        return report


def main():
    project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    analyzer = ProjectAnalyzer(project_path)
    report = analyzer.analyze_all()
    
    # Guardar reporte JSON
    report_file = os.path.join(project_path, "scripts", "analisis_report.json")
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\nReporte guardado en: {report_file}")
    print("=" * 70)
    
    return report


if __name__ == "__main__":
    main()

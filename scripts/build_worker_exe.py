#!/usr/bin/env python3
"""
SynapseIA - Worker EXE Builder
Crea un ejecutable auto-contenido para el Worker con todas las dependencias.
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

def install_pyinstaller():
    """Instala PyInstaller si no está disponible."""
    try:
        import PyInstaller
        print("✅ PyInstaller ya está instalado")
    except ImportError:
        print("📦 Instalando PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)

def create_worker_exe():
    """Crea el ejecutable del Worker."""
    project_root = Path(__file__).parent.parent
    backend_dir = project_root / "backend"
    
    # Verificar que el backend existe
    if not backend_dir.exists():
        print(f"❌ Directorio backend no encontrado: {backend_dir}")
        return False
    
    # Directorio de trabajo para PyInstaller
    os.chdir(project_root)
    
    # Usar forward slashes para evitar problemas de escape en spec
    root_path = str(project_root).replace('\\', '/')
    
    # Archivo spec para PyInstaller - usar forward slashes
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['backend/main.py'],
    pathex=['{root_path}'],
    binaries=[],
    datas=[
        ('backend/api', 'backend/api'),
        ('backend/engine', 'backend/engine'),
        ('backend/network', 'backend/network'),
        ('backend/database', 'backend/database'),
        ('backend/services', 'backend/services'),
        ('backend/adapters', 'backend/adapters'),
        ('backend/memory', 'backend/memory'),
        ('backend/config.py', 'backend'),
        ('backend/models.py', 'backend'),
    ],
    hiddenimports=[
        'uvicorn',
        'fastapi',
        'sqlalchemy',
        'aiosqlite',
        'httpx',
        'structlog',
        'asyncio',
        'json',
        'socket',
        'psutil',
        'win32api',
        'win32security',
        'win32con',
        'win32gui',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SynapseWorker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None
)
'''
    
    # Escribir archivo spec
    spec_file = project_root / "SynapseWorker.spec"
    with open(spec_file, 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print(f"📝 Archivo spec creado: {spec_file}")
    
    # Construir el EXE
    print("🔨 Construyendo SynapseWorker.exe...")
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        str(spec_file)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("✅ Build exitoso!")
        
        # Verificar que se creó el exe
        exe_path = project_root / "dist" / "SynapseWorker.exe"
        if exe_path.exists():
            print(f"📦 EXE creado: {exe_path}")
            print(f"📏 Tamaño: {exe_path.stat().st_size / (1024*1024):.1f} MB")
            
            # Copiar a scripts para fácil acceso
            scripts_dir = project_root / "scripts"
            target_path = scripts_dir / "SynapseWorker.exe"
            shutil.copy2(exe_path, target_path)
            print(f"📋 Copiado a: {target_path}")
            
            return True
        else:
            print("❌ No se encontró el EXE generado")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Error en PyInstaller: {e}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False

def create_worker_bat():
    """Crea un batch file para iniciar el Worker fácilmente."""
    project_root = Path(__file__).parent.parent
    scripts_dir = project_root / "scripts"
    
    bat_content = '''@echo off
title SynapseIA Worker
echo Iniciando Synapse Worker...
echo.
echo Este es el backend del Worker para SynapseIA
echo Se conectará automáticamente con el Master
echo.

REM Establecer variables de entorno
set NODE_ROLE=WORKER
set WORKER_HOST=%COMPUTERNAME%

REM Iniciar el backend
SynapseWorker.exe

pause
'''
    
    bat_path = scripts_dir / "StartWorker.bat"
    with open(bat_path, 'w', encoding='utf-8') as f:
        f.write(bat_content)
    
    print(f"📋 Batch creado: {bat_path}")

def main():
    """Función principal."""
    print("=" * 60)
    print("SYNAPSEIA - WORKER EXE BUILDER")
    print("=" * 60)
    
    # 1. Instalar PyInstaller
    install_pyinstaller()
    
    # 2. Crear el EXE
    if create_worker_exe():
        # 3. Crear batch file
        create_worker_bat()
        
        print("\n" + "=" * 60)
        print("✅ WORKER EXE CREADO EXITOSAMENTE")
        print("=" * 60)
        print("Archivos generados:")
        print("  📦 SynapseWorker.exe (backend completo)")
        print("  📋 StartWorker.bat (inicio fácil)")
        print("\nPara usar:")
        print("1. Copiar SynapseWorker.exe al Worker")
        print("2. Ejecutar StartWorker.bat o SynapseWorker.exe")
        print("3. El Worker se conectará automáticamente con el Master")
    else:
        print("\n❌ Falló la creación del EXE")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

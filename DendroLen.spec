# -*- mode: python ; coding: utf-8 -*-
# DendroLen.spec — PyInstaller spec file para Windows
# Ejecutar con:  pyinstaller DendroLen.spec

import sys
from pathlib import Path

block_cipher = None

# ── Archivos fuente ───────────────────────────────────────────────────────────
src_dir = Path('.')  # Ejecutar desde la carpeta del proyecto

a = Analysis(
    ['main_dendro.py'],
    pathex=[str(src_dir)],
    binaries=[],
    datas=[('DendroLen.ico', '.')],
    hiddenimports=[
        # PyQt6
        'PyQt6.QtWidgets',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        # Matplotlib backends
        'matplotlib.backends.backend_qtagg',
        'matplotlib.backends.backend_agg',
        # Serial
        'serial',
        'serial.tools',
        'serial.tools.list_ports',
        'serial.tools.list_ports_windows',
        'serial.tools.list_ports_common',
        # Pandas / NumPy / openpyxl (para serie maestra)
        'pandas',
        'numpy',
        'openpyxl',
        # Módulos del proyecto (por si los imports dinámicos no se detectan)
        'constantes',
        'tema_manager',
        'ventana_principal',
        'dialogo_config',
        'dialogo_nueva_muestra',
        'dialogo_ayuda',
        'panel_medicion',
        'serial_worker',
        'serie_maestra',
        'tucson_writer',
        'modulo_unir',
        'cronologia',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Excluir módulos innecesarios para reducir tamaño
        'tkinter',
        '_tkinter',
        'xmlrpc',
        'pydoc',
        'doctest',
        'IPython',
        'jupyter',
        'notebook',
        'sphinx',
        'pytest',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],                     # NO incluir binarios aquí (modo onedir)
    exclude_binaries=True,  # modo onedir (más fácil de depurar)
    name='DendroLen',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,          # Sin ventana de consola
    icon='DendroLen.ico' if Path('DendroLen.ico').exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='DendroLen',
)

# -*- mode: python ; coding: utf-8 -*-
# DendroLen_onefile.spec — Genera UN SOLO .exe (más lento al iniciar, más fácil de distribuir)
# Ejecutar con:  pyinstaller DendroLen_onefile.spec

from pathlib import Path

block_cipher = None

a = Analysis(
    ['main_dendro.py'],
    pathex=['.'],
    binaries=[],
    datas=[('DendroLen.ico', '.')],
    hiddenimports=[
        'PyQt6.QtWidgets', 'PyQt6.QtCore', 'PyQt6.QtGui',
        'matplotlib.backends.backend_qtagg', 'matplotlib.backends.backend_agg',
        'serial', 'serial.tools', 'serial.tools.list_ports',
        'serial.tools.list_ports_windows', 'serial.tools.list_ports_common',
        'pandas', 'numpy', 'openpyxl',
        'constantes', 'tema_manager', 'ventana_principal',
        'dialogo_config', 'dialogo_nueva_muestra', 'dialogo_ayuda',
        'panel_medicion', 'serial_worker', 'serie_maestra', 'tucson_writer',
        'modulo_unir', 'cronologia',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=['tkinter', '_tkinter', 'IPython', 'jupyter', 'sphinx', 'pytest'],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,         # TODO incluido en el .exe
    a.zipfiles,
    a.datas,
    [],
    name='DendroLen',
    debug=False,
    strip=False,
    upx=True,
    console=False,      # Sin ventana de consola
    icon='DendroLen.ico' if Path('DendroLen.ico').exists() else None,
)

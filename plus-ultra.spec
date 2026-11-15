# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

block_cipher = None

# Hidden imports required across platforms
hidden_imports = [
    'tkinter',
    'tkinter.ttk',
    'sqlite3',
    'sqlalchemy',
    'sqlalchemy.sql.default_comparator',
    'pystray',
    'PIL',
    'PIL._imagingtk',
    'plus_ultra.platform',
    'plus_ultra.platform.detection',
    'plus_ultra.platform.capabilities',
    'plus_ultra.platform.factory',
    'plus_ultra.core.application',
]

if sys.platform == 'win32':
    hidden_imports.extend([
        'pystray._win32',
        'winreg',
        'msvcrt',
        'plus_ultra.platform.windows',
    ])
else:
    hidden_imports.extend([
        'fcntl',
        'plus_ultra.platform.linux',
    ])

icon_file = 'src/plus_ultra/resources/icons/app.ico' if sys.platform == 'win32' else None

a = Analysis(
    ['src/plus_ultra/main.py'],
    pathex=['src'],
    binaries=[],
    datas=[('src/plus_ultra/resources', 'plus_ultra/resources')],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='plus-ultra',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
)

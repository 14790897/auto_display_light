# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

block_cipher = None

# 强制收集 tkinter Tcl/Tk DLL（CI 环境 Windows Server 可能缺少 GUI 库）
tk_datas = collect_data_files('tkinter')
tk_bins = collect_dynamic_libs('tkinter')

a = Analysis(
    ['autolight_tray.py'],
    pathex=[],
    binaries=tk_bins,
    datas=tk_datas,
    hiddenimports=['requests', 'tkinter', '_tkinter', 'pystray', 'PIL', 'PIL.Image', 'PIL.ImageDraw',
                   'six', 'pkg_resources', 'jaraco', 'jaraco.classes', 'more_itertools', 'winreg'],
    hookspath=[],
    hooksconfig={},
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
    name='AutoDisplayLight',
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
    icon='autolight.ico',
)

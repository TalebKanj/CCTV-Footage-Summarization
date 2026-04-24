# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files, collect_dynamic_libs
from PyInstaller import *

block_cipher = None

# Collect PySide6 submodules
pyqt6_submodules = collect_submodules('PySide6')
pyqt6_datas = collect_data_files('PySide6', include_py_files=True)
pyqt6_binaries = collect_dynamic_libs('PySide6')

a = Analysis(
    ['app/ui_pyside6/wrapper_entry.py'],
    pathex=[os.path.abspath('.')],
    binaries=pyqt6_binaries,
    datas=[
        # Assets folder
        ('assets', 'assets'),
        # Config files
        ('app/config.py', 'app'),
        ('custom_bytetrack.yaml', '.'),
    ] + pyqt6_datas,
    hiddenimports=[
        # PySide6
        'PySide6',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtWinExtras',
        # Core dependencies
        'cv2',
        'cv2.cv2',
        'numpy',
        'numpy.core._multiarray_umath',
        'ultralytics',
        'ultralytics.yolo',
        'PIL',
        'PIL.Image',
    ] + pyqt6_submodules,
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
    [],
    exclude_binaries=True,
    name='CCTVAnalyzer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CCTVAnalyzer',
)
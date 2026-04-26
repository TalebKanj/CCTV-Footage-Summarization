# -*- mode: python ; coding: utf-8 -*-
import os

from PyInstaller.building.datastruct import Tree
from PyInstaller.utils.hooks import collect_submodules, collect_data_files, collect_dynamic_libs

block_cipher = None

# Collect PySide6 submodules and Qt plugins (needed for QMediaPlayer/QVideoSink, etc.)
pyside6_submodules = collect_submodules("PySide6")
pyside6_datas = collect_data_files("PySide6", include_py_files=True)
pyside6_binaries = collect_dynamic_libs("PySide6")

qt_plugin_binaries = []
try:
    import PySide6  # type: ignore

    pyside6_dir = os.path.dirname(PySide6.__file__)
    qt_plugins_dir = os.path.join(pyside6_dir, "Qt", "plugins")
    if os.path.isdir(qt_plugins_dir):
        # Bundle all Qt plugins as binaries to avoid runtime "no platform plugin" / multimedia backend issues.
        qt_plugin_binaries = Tree(qt_plugins_dir, prefix="PySide6/Qt/plugins", typecode="BINARY")
except Exception:
    qt_plugin_binaries = []

a = Analysis(
    ['main.py'],
    pathex=[os.path.abspath('.')],
    binaries=pyside6_binaries + qt_plugin_binaries,
    datas=[
        # Assets folder
        ('assets', 'assets'),
        # Runtime resources / configs
        ('custom_bytetrack.yaml', '.'),
        ('prompts.txt', '.'),
    ] + pyside6_datas,
    hiddenimports=[
        # PySide6
        'PySide6',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtWinExtras',
        'PySide6.QtMultimedia',
        'PySide6.QtMultimediaWidgets',
        'PySide6.QtNetwork',
        # Core dependencies
        'cv2',
        'cv2.cv2',
        'numpy',
        'numpy.core._multiarray_umath',
        'ultralytics',
        'ultralytics.yolo',
        'huggingface_hub',
        'PIL',
        'PIL.Image',
    ] + pyside6_submodules,
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

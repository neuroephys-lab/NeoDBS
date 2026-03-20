# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import (
    collect_all,
    collect_submodules,
    collect_data_files,
)

from pathlib import Path
import sys

ROOT = Path(SPECPATH).resolve()

# --- Datas (images, fonts, and package data) ---
datas = [
    (str(ROOT / 'src' / 'NeoDBS.png'), '.')
]

# Include all fonts
fonts_dir = ROOT / 'src' / 'fonts'
datas += [(str(p), 'fonts') for p in fonts_dir.rglob('*') if p.is_file()]

# --- Icon based on platform ---
if sys.platform == "win32":
    icon_file = str(ROOT / "NeoDBS.ico")
elif sys.platform == "darwin":
    icon_file = str(ROOT / "NeoDBS.icns")
else:
    icon_file = None  # Linux

# --- Collect MNE and DearPyGui ---
mne_datas, mne_binaries, mne_hiddenimports = collect_all('mne')
datas += mne_datas
binaries = mne_binaries
hiddenimports = mne_hiddenimports

dpg_datas, dpg_binaries, dpg_hiddenimports = collect_all('dearpygui')
datas += dpg_datas
binaries += dpg_binaries
hiddenimports += dpg_hiddenimports

# --- Exclusions ---
excludes = [
    "mayavi",
    "pyvista",
    "vtk",
    "mne.viz",
    "matplotlib.backends.backend_qt5agg",
]

# --- Analysis ---
a = Analysis(
    [str(ROOT / 'src' / 'neodbs' / '__main__.py')],
    pathex=[str(ROOT / 'src')],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='NeoDBS',
    debug=True,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
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
# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import (
    collect_all,
    collect_submodules,
    collect_data_files,
)

from pathlib import Path
import sys

ROOT = Path(SPECPATH).resolve()


datas = [(str(ROOT / 'src' / 'NeoDBS.png'), '.')]

if sys.platform == "win32":
    icon_file = str(ROOT / "NeoDBS.ico")
elif sys.platform == "darwin":
    icon_file = str(ROOT / "NeoDBS.icns")
else:
    icon_file = None  # Linux

binaries = []
hiddenimports = []

# --- MNE (minimal, time_frequency-focused) ---
#hiddenimports += collect_submodules("mne.time_frequency")
#hiddenimports += collect_submodules("mne.utils")
#hiddenimports += collect_submodules("mne.filter")
#hiddenimports += collect_submodules("mne.baseline")
#hiddenimports += collect_submodules("mne.parallel")
#hiddenimports += collect_submodules("mne.externals")

# --- Required runtime data ---
fonts_dir = ROOT / 'src' / 'fonts'

datas += [
    (str(p), 'fonts')
    for p in fonts_dir.rglob('*')
    if p.is_file()
]

datas += collect_data_files("mne")
datas += collect_data_files("dearpygui")

# --- Exclusions ---
excludes = [
    "mayavi",
    "pyvista",
    "vtk",
    "mne.viz",
    "mne.utils._logging",
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
    debug=False,
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
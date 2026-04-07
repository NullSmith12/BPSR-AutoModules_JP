# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path
import tempfile

from PyInstaller.utils.hooks import collect_data_files, collect_submodules


def configure_scapy_cache_home():
    if os.environ.get("XDG_CACHE_HOME"):
        return

    for root in (os.environ.get("LOCALAPPDATA"), tempfile.gettempdir()):
        if not root:
            continue

        try:
            cache_home = Path(root) / "BPSR-AutoModules"
            cache_home.mkdir(parents=True, exist_ok=True)
            os.environ["XDG_CACHE_HOME"] = str(cache_home)
            return
        except OSError:
            continue


configure_scapy_cache_home()

APP_EXE_NAME = "BPSR-AutoModules_JP"
APP_DIST_DIR = "gui_app"


datas = [
    ("icon.ico", "."),
    ("icon.png", "."),
    ("Font Awesome 7 Free-Solid-900.otf", "."),
    ("custom_presets.json", "."),
    ("Fix Names.json", "."),
    ("Back.webp", "."),
    ("LICENSE", "."),
    ("README.md", "."),
    ("Icons", "Icons"),
    ("Modulos", "Modulos"),
    ("Module-Effects", "Module-Effects"),
    ("locales", "locales"),
]

datas += collect_data_files("customtkinter")

hiddenimports = [
    "network_interface_util",
    "star_resonance_monitor_core",
    "logging_config",
    "module_optimizer",
    "module_parser",
    "module_types",
    "packet_capture",
    "star_railway_monitor",
    "BlueProtobuf_pb2",
    "zstandard.backend_cffi",
    "zstandard._cffi",
]

hiddenimports += collect_submodules("scapy")


a = Analysis(
    ["gui_app.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_EXE_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=["icon.ico"],
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=APP_DIST_DIR,
)

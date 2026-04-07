import sys
import shutil
import tempfile
from cx_Freeze import setup, Executable


def _patch_tempfile_cleanup_for_windows():
    """cx_Freeze 実行後の一時ディレクトリ削除失敗を回避する。"""
    if sys.platform != "win32":
        return

    def _safe_rmtree(cls, name, ignore_errors=False, repeated=False):
        shutil.rmtree(name, ignore_errors=True)

    tempfile.TemporaryDirectory._rmtree = classmethod(_safe_rmtree)


_patch_tempfile_cleanup_for_windows()

# cx_Freeze が自動検出しきれない依存関係を明示する
build_exe_options = {
    "packages": ["tkinter", "customtkinter", "PIL", "scapy", "logging", "os", "json", "threading", "queue", "sys"],
    "includes": [
        "network_interface_util",
        "star_resonance_monitor_core",
        "logging_config",
        "module_optimizer",
        "module_parser",
        "module_types",
        "packet_capture",
        "star_railway_monitor",
        "BlueProtobuf_pb2",
    ],
    "include_files": [
        "icon.ico",
        "icon.png",
        "Font Awesome 7 Free-Solid-900.otf",
        ("Icons", "Icons"),
        ("Modulos", "Modulos"),
        ("Module-Effects", "Module-Effects"),
        "custom_presets.json",
        "Fix Names.json", # Asegurarse de incluir este archivo de datos
        "Back.webp", # Asegurarse de incluir esta imagen
        "LICENSE", # Incluir la licencia
        "README.md", # Incluir el README
    ],
    "build_exe": "build/exe",
    "excludes": [],
    "optimize": 0,
}

# Windows ではコンソールを非表示にする
base = None
if sys.platform == "win32":
    base = "gui"

setup(
    name="BPSR Module Optimizer",
    version="1.0",
    description="BPSR モジュール最適化ツール by: MrSnake",
    options={"build_exe": build_exe_options},
    executables=[Executable("gui_app.py", base=base, icon="icon.ico")],
)

"""Utilidades de archivos y rutas (sin dependencias de la interfaz)."""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

APP_NAME = "PDF_MASTER"

_RESERVED = {"CON", "PRN", "AUX", "NUL"} | {f"COM{i}" for i in range(1, 10)} | {f"LPT{i}" for i in range(1, 10)}


def resource_path(relative: str) -> str:
    """Ruta a un recurso, válida tanto en desarrollo como dentro del .exe de PyInstaller."""
    base = getattr(sys, "_MEIPASS", None) or Path(__file__).resolve().parent.parent
    return str(Path(base) / relative)


def app_data_dir() -> Path:
    """Carpeta donde se guardan el historial y la configuración."""
    base = os.environ.get("APPDATA")
    root = Path(base) if base else Path.home() / ".config"
    folder = root / APP_NAME
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def documents_dir() -> str:
    for candidate in (Path.home() / "Documents", Path.home() / "Documentos", Path.home()):
        if candidate.is_dir():
            return str(candidate)
    return str(Path.home())


def has_extension(path: str, extensions: tuple[str, ...]) -> bool:
    return os.path.splitext(path)[1].lower() in extensions


def filter_by_extension(paths, extensions):
    """Separa los archivos válidos (existen y tienen extensión permitida) de los rechazados."""
    valid, rejected = [], []
    for p in paths:
        if os.path.isfile(p) and has_extension(p, extensions):
            valid.append(p)
        else:
            rejected.append(p)
    return valid, rejected


def sanitize_filename(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip().rstrip(". ")
    if name.upper().split(".")[0] in _RESERVED:
        name = "_" + name
    return name


def ensure_extension(name: str, ext: str = ".pdf") -> str:
    return name if name.lower().endswith(ext) else name + ext


def unique_path(path: str) -> str:
    base, ext = os.path.splitext(path)
    candidate, n = path, 1
    while os.path.exists(candidate):
        candidate = f"{base} ({n}){ext}"
        n += 1
    return candidate


def same_file(a: str, b: str) -> bool:
    try:
        if os.path.exists(a) and os.path.exists(b):
            return os.path.samefile(a, b)
    except OSError:
        pass
    return os.path.normcase(os.path.abspath(a)) == os.path.normcase(os.path.abspath(b))


def open_folder(path: str) -> bool:
    """Abre el explorador mostrando el archivo (o la carpeta) indicado."""
    path = os.path.normpath(path)
    if not os.path.exists(path):
        path = os.path.dirname(path)
        if not os.path.isdir(path):
            return False
    try:
        if sys.platform.startswith("win"):
            if os.path.isfile(path):
                subprocess.Popen(["explorer", f"/select,{path}"])
            else:
                os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", "-R", path] if os.path.isfile(path) else ["open", path])
        else:
            subprocess.Popen(["xdg-open", path if os.path.isdir(path) else os.path.dirname(path)])
        return True
    except OSError:
        return False


def open_file(path: str) -> bool:
    if not os.path.isfile(path):
        return False
    try:
        if sys.platform.startswith("win"):
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
        return True
    except OSError:
        return False

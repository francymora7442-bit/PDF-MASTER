"""Configuración de la aplicación guardada en %APPDATA%\\PDF_MASTER\\config.json."""
from __future__ import annotations

import json
import os

from utils.file_manager import app_data_dir, documents_dir

DEFAULTS = {
    "output_dir": "",            # vacío = carpeta Documentos
    "page_size": "A4",           # A4 | LETTER | ORIGINAL
    "orientation": "vertical",   # vertical | horizontal | auto
    "png_background": "#FFFFFF",
    "history_limit": 100,
}


class SettingsManager:
    def __init__(self):
        self._path = app_data_dir() / "config.json"
        self._data = dict(DEFAULTS)
        self._load()

    def _load(self):
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return
        if isinstance(data, dict):
            for key in DEFAULTS:
                if key in data:
                    self._data[key] = data[key]

    def get(self, key):
        return self._data.get(key, DEFAULTS.get(key))

    def update(self, **values):
        self._data.update(values)
        self.save()

    def reset(self):
        self._data = dict(DEFAULTS)
        self.save()

    def save(self):
        try:
            self._path.write_text(json.dumps(self._data, indent=2, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass

    def output_dir(self) -> str:
        d = self.get("output_dir")
        return d if d and os.path.isdir(d) else documents_dir()

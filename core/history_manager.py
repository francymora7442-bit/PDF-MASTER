"""Historial de documentos procesados (JSON local)."""
from __future__ import annotations

import json
import os
from datetime import datetime

from utils.file_manager import app_data_dir


class HistoryManager:
    def __init__(self, limit: int = 100):
        self._path = app_data_dir() / "history.json"
        self._limit = max(1, int(limit))
        self._entries = self._load()

    def _load(self):
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return []
        return [e for e in data if isinstance(e, dict) and "path" in e] if isinstance(data, list) else []

    def _save(self):
        tmp = str(self._path) + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump(self._entries, fh, indent=2, ensure_ascii=False)
            os.replace(tmp, self._path)
        except OSError:
            pass

    def set_limit(self, limit: int):
        self._limit = max(1, int(limit))
        self._entries = self._entries[: self._limit]
        self._save()

    def add(self, operation: str, output_path: str):
        self._entries.insert(
            0,
            {
                "name": os.path.basename(output_path),
                "operation": operation,
                "date": datetime.now().isoformat(timespec="seconds"),
                "path": output_path,
            },
        )
        self._entries = self._entries[: self._limit]
        self._save()

    def entries(self):
        return list(self._entries)

    def clear(self):
        self._entries = []
        self._save()

"""Módulo 5: Historial de archivos procesados."""
from __future__ import annotations

import os
from datetime import datetime

from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView, QHBoxLayout, QHeaderView, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from ui import dialogs
from ui.widgets import make_button, page_header
from utils import file_manager as fm


class HistoryPage(QWidget):
    COLUMNS = ("Archivo", "Operación", "Fecha", "Ubicación")

    def __init__(self, history, parent=None):
        super().__init__(parent)
        self.history = history
        self._entries = []
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 20)
        root.setSpacing(12)
        root.addWidget(page_header("Historial de archivos",
                                   "Últimos documentos procesados. Doble clic para abrir la carpeta donde se guardaron."))

        bar = QHBoxLayout()
        bar.addWidget(make_button("📂  Abrir carpeta", "primary", "Abrir la carpeta del archivo seleccionado", self._open_folder, 42))
        bar.addWidget(make_button("📄  Abrir archivo", slot=self._open_file, height=42))
        bar.addWidget(make_button("🔄  Actualizar", slot=self.refresh, height=42))
        bar.addStretch(1)
        bar.addWidget(make_button("🗑  Limpiar historial", "danger", slot=self._clear, height=42))
        root.addLayout(bar)

        self.table = QTableWidget(0, len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().hide()
        self.table.setShowGrid(False)
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 280)
        self.table.cellDoubleClicked.connect(lambda *_: self._open_folder())
        root.addWidget(self.table, 1)
        self.refresh()

    def refresh(self):
        self._entries = self.history.entries()
        self.table.setRowCount(len(self._entries))
        for row, e in enumerate(self._entries):
            try:
                date = datetime.fromisoformat(e.get("date", "")).strftime("%d/%m/%Y  %H:%M")
            except ValueError:
                date = e.get("date", "")
            path = e.get("path", "")
            exists = os.path.exists(path)
            values = (e.get("name", os.path.basename(path)), e.get("operation", ""), date,
                      path if exists else f"{path}   (ya no existe)")
            for col, text in enumerate(values):
                item = QTableWidgetItem(text)
                item.setToolTip(path)
                if not exists:
                    item.setForeground(QColor("#9CA3AF"))
                self.table.setItem(row, col, item)

    def _selected(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self._entries):
            dialogs.show_warning(self, "Selecciona un elemento de la lista.")
            return None
        return self._entries[row]

    def _open_folder(self):
        entry = self._selected()
        if entry is None:
            return
        if not fm.open_folder(entry["path"]):
            dialogs.show_error(self, "La carpeta de ese archivo ya no existe.")
        elif not os.path.exists(entry["path"]):
            dialogs.show_info(self, "El archivo ya no está en esa ubicación; se abrió su carpeta.")

    def _open_file(self):
        entry = self._selected()
        if entry is None:
            return
        if not fm.open_file(entry["path"]):
            dialogs.show_error(self, "No se pudo abrir el archivo. Puede que ya no exista.")

    def _clear(self):
        if not self._entries:
            return
        if dialogs.confirm(self, "Limpiar historial",
                           "Se borrará la lista del historial (los archivos no se eliminan). ¿Continuar?", yes="Limpiar"):
            self.history.clear()
            self.refresh()

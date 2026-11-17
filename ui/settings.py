"""Configuración de la aplicación."""
from __future__ import annotations

import os

from PySide6.QtCore import Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QColorDialog, QComboBox, QFileDialog, QFormLayout, QFrame, QGroupBox, QHBoxLayout, QLineEdit, QSpinBox,
    QVBoxLayout, QWidget,
)

from ui import dialogs
from ui.widgets import make_button, page_header
from utils import file_manager as fm


class SettingsPage(QWidget):
    saved = Signal()

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self._bg_hex = "#FFFFFF"
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 20)
        root.setSpacing(14)
        root.addWidget(page_header("Configuración", "Valores predeterminados que usarán las herramientas."))

        group = QGroupBox("Preferencias")
        form = QFormLayout(group)
        form.setVerticalSpacing(12)

        folder_row = QHBoxLayout()
        self.folder_edit = QLineEdit()
        self.folder_edit.setPlaceholderText("Vacío = carpeta Documentos")
        folder_row.addWidget(self.folder_edit, 1)
        folder_row.addWidget(make_button("Examinar…", slot=self._browse, height=36))
        folder_row.addWidget(make_button("Restablecer", slot=lambda: self.folder_edit.clear(), height=36))
        form.addRow("Carpeta de destino:", folder_row)

        self.size_combo = QComboBox()
        for text, data in (("A4", "A4"), ("Carta", "LETTER"), ("Tamaño original", "ORIGINAL")):
            self.size_combo.addItem(text, data)
        form.addRow("Tamaño de página (imágenes):", self.size_combo)

        self.orient_combo = QComboBox()
        for text, data in (("Vertical", "vertical"), ("Horizontal", "horizontal"), ("Automática", "auto")):
            self.orient_combo.addItem(text, data)
        form.addRow("Orientación (imágenes):", self.orient_combo)

        bg_row = QHBoxLayout()
        self.swatch = QFrame()
        self.swatch.setFixedSize(28, 28)
        bg_row.addWidget(self.swatch)
        bg_row.addWidget(make_button("Elegir color…", slot=self._pick_color, height=36))
        bg_row.addStretch(1)
        form.addRow("Fondo predeterminado PNG:", bg_row)

        self.limit_spin = QSpinBox()
        self.limit_spin.setRange(10, 500)
        self.limit_spin.setSuffix(" registros")
        form.addRow("Tamaño del historial:", self.limit_spin)
        root.addWidget(group)

        row = QHBoxLayout()
        row.addWidget(make_button("Guardar configuración", "primary", slot=self._save, height=46))
        row.addWidget(make_button("Valores de fábrica", slot=self._factory, height=46))
        row.addStretch(1)
        root.addLayout(row)
        root.addStretch(1)
        self.load()

    def load(self):
        self.folder_edit.setText(self.settings.get("output_dir") or "")
        for combo, key in ((self.size_combo, "page_size"), (self.orient_combo, "orientation")):
            idx = combo.findData(self.settings.get(key))
            combo.setCurrentIndex(max(idx, 0))
        self._set_bg(self.settings.get("png_background") or "#FFFFFF")
        self.limit_spin.setValue(int(self.settings.get("history_limit") or 100))

    def _set_bg(self, hex_color):
        self._bg_hex = hex_color
        self.swatch.setStyleSheet(f"background: {hex_color}; border: 1px solid #9CA3AF; border-radius: 6px;")

    def _pick_color(self):
        color = QColorDialog.getColor(QColor(self._bg_hex), self, "Color de fondo")
        if color.isValid():
            self._set_bg(color.name())

    def _browse(self):
        d = QFileDialog.getExistingDirectory(self, "Carpeta de destino predeterminada",
                                             self.folder_edit.text() or fm.documents_dir())
        if d:
            self.folder_edit.setText(os.path.normpath(d))

    def _save(self):
        folder = self.folder_edit.text().strip()
        if folder and not os.path.isdir(folder):
            dialogs.show_warning(self, "La carpeta indicada no existe. Elige otra o déjala vacía.")
            return
        self.settings.update(
            output_dir=folder,
            page_size=self.size_combo.currentData(),
            orientation=self.orient_combo.currentData(),
            png_background=self._bg_hex,
            history_limit=self.limit_spin.value(),
        )
        self.saved.emit()
        dialogs.show_info(self, "✔ Configuración guardada.")

    def _factory(self):
        if dialogs.confirm(self, "Valores de fábrica", "¿Restablecer toda la configuración?", yes="Restablecer"):
            self.settings.reset()
            self.load()
            self.saved.emit()

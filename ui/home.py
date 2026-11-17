"""Pantalla de inicio."""
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QGridLayout, QLabel, QVBoxLayout, QWidget

from ui.widgets import make_button, page_header


class HomePage(QWidget):
    navigate = Signal(int)

    def __init__(self, targets, parent=None):
        """targets: lista de (texto, descripción, índice_de_página)."""
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(36, 32, 36, 24)
        root.setSpacing(18)
        root.addWidget(page_header("Bienvenido a PDF MASTER",
                                   "Gestiona tus documentos PDF e imágenes desde un solo lugar. "
                                   "Elige una herramienta para empezar."))
        grid = QGridLayout()
        grid.setSpacing(16)
        for i, (title, desc, index) in enumerate(targets):
            btn = make_button(f"{title}\n{desc}", "card", height=110)
            btn.clicked.connect(lambda _=False, idx=index: self.navigate.emit(idx))
            grid.addWidget(btn, i // 2, i % 2)
        root.addLayout(grid)
        note = QLabel("🔒  Todo se procesa en tu ordenador: ningún documento se sube a Internet "
                      "y los archivos originales nunca se sobrescriben.")
        note.setObjectName("Hint")
        note.setWordWrap(True)
        root.addWidget(note)
        root.addStretch(1)

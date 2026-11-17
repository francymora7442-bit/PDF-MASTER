"""Componentes reutilizables de la interfaz."""
from __future__ import annotations

import os

from PySide6.QtCore import QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QAbstractItemView, QFileDialog, QHBoxLayout, QLabel, QLineEdit, QListView,
    QListWidget, QProgressBar, QPushButton, QVBoxLayout, QWidget,
)

from utils import file_manager as fm

ROLE_PATH = int(Qt.ItemDataRole.UserRole)
ROLE_PWD = ROLE_PATH + 1
ROLE_PAGES = ROLE_PATH + 2


def make_button(text, role=None, tooltip="", slot=None, height=40):
    btn = QPushButton(text)
    if role:
        btn.setProperty("role", role)
    if tooltip:
        btn.setToolTip(tooltip)
    btn.setMinimumHeight(height)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    if slot:
        btn.clicked.connect(slot)
    return btn


def page_header(title, subtitle=""):
    w = QWidget()
    lay = QVBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 6)
    lay.setSpacing(2)
    t = QLabel(title)
    t.setObjectName("PageTitle")
    lay.addWidget(t)
    if subtitle:
        s = QLabel(subtitle)
        s.setObjectName("PageSubtitle")
        s.setWordWrap(True)
        lay.addWidget(s)
    return w


def move_selected_rows(lw: QListWidget, delta: int) -> bool:
    """Mueve las filas seleccionadas un lugar (delta=-1 arriba/izquierda, +1 abajo/derecha)."""
    rows = sorted(i.row() for i in lw.selectedIndexes())
    if not rows:
        return False
    if delta < 0:
        if rows[0] == 0:
            return False
        for r in rows:
            lw.insertItem(r - 1, lw.takeItem(r))
    else:
        if rows[-1] == lw.count() - 1:
            return False
        for r in reversed(rows):
            lw.insertItem(r + 1, lw.takeItem(r))
    lw.clearSelection()
    for r in rows:
        lw.item(r + delta).setSelected(True)
    lw.setCurrentRow(rows[0] + delta)
    lw.scrollToItem(lw.item(rows[0] + delta))
    return True


class _HintDropList(QListWidget):
    """Lista que acepta archivos arrastrados desde el Explorador y muestra un texto cuando está vacía."""

    files_dropped = Signal(list)

    def __init__(self, hint="", parent=None):
        super().__init__(parent)
        self._hint = hint
        self.setAcceptDrops(True)

    def _is_external(self, event):
        return event.source() is not self and event.mimeData().hasUrls()

    def dragEnterEvent(self, event):
        if self._is_external(event):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if self._is_external(event):
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if self._is_external(event):
            paths = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
            event.acceptProposedAction()
            if paths:  # diferido para no bloquear al Explorador con diálogos modales
                QTimer.singleShot(0, lambda p=paths: self.files_dropped.emit(p))
        else:
            self._internal_drop(event)

    def _internal_drop(self, event):
        super().dropEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.count() == 0 and self._hint:
            painter = QPainter(self.viewport())
            painter.setPen(QColor("#9CA3AF"))
            painter.drawText(self.viewport().rect(), Qt.AlignmentFlag.AlignCenter, self._hint)
            painter.end()


class DropListWidget(_HintDropList):
    """Lista vertical reordenable (arrastrando) que también acepta archivos externos."""

    def __init__(self, hint="", icon_size=0, parent=None):
        super().__init__(hint, parent)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setSpacing(2)
        if icon_size:
            self.setIconSize(QSize(icon_size, icon_size))


class PageGridWidget(_HintDropList):
    """Cuadrícula de miniaturas de páginas con reordenación por arrastre (varias a la vez)."""

    order_changed = Signal()

    def __init__(self, hint="", parent=None):
        super().__init__(hint, parent)
        self.setViewMode(QListView.ViewMode.IconMode)
        self.setResizeMode(QListView.ResizeMode.Adjust)
        self.setMovement(QListView.Movement.Static)
        self.setFlow(QListView.Flow.LeftToRight)
        self.setWrapping(True)
        self.setUniformItemSizes(True)
        self.setWordWrap(True)
        self.setSpacing(8)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setDropIndicatorShown(True)

    def selected_rows(self):
        return sorted(i.row() for i in self.selectedIndexes())

    def move_rows_to(self, rows, target):
        """Mueve las filas indicadas para que queden juntas antes de la posición 'target'."""
        rows = sorted(set(rows))
        if not rows:
            return
        items = [self.takeItem(r) for r in reversed(rows)]
        items.reverse()
        insert_at = target - sum(1 for r in rows if r < target)
        insert_at = max(0, min(insert_at, self.count()))
        self.clearSelection()
        for offset, it in enumerate(items):
            self.insertItem(insert_at + offset, it)
            it.setSelected(True)
        self.scrollToItem(items[0])

    def _target_row(self, pos):
        for r in range(self.count()):
            rect = self.visualRect(self.model().index(r, 0))
            if pos.y() < rect.top():
                return r
            if pos.y() <= rect.bottom() and pos.x() < rect.center().x():
                return r
        return self.count()

    def _internal_drop(self, event):
        rows = self.selected_rows()
        if rows:
            self.move_rows_to(rows, self._target_row(event.position().toPoint()))
            self.order_changed.emit()
        event.setDropAction(Qt.DropAction.IgnoreAction)  # evita que Qt borre los originales
        event.accept()
        try:
            self.setState(QAbstractItemView.State.NoState)
        except Exception:  # noqa: BLE001
            pass
        self.viewport().update()


class OutputSelector(QWidget):
    """Nombre del archivo final + carpeta de destino."""

    def __init__(self, default_name="documento", parent=None):
        super().__init__(parent)
        self._folder_user_set = False
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)
        lay.addWidget(QLabel("Nombre del archivo final"))
        row = QHBoxLayout()
        self.name_edit = QLineEdit(default_name)
        self.name_edit.setPlaceholderText("Ej.: documento_final")
        row.addWidget(self.name_edit, 1)
        row.addWidget(QLabel(".pdf"))
        lay.addLayout(row)
        lay.addWidget(QLabel("Carpeta de destino"))
        row2 = QHBoxLayout()
        self.folder_edit = QLineEdit()
        self.folder_edit.setPlaceholderText("Selecciona una carpeta…")
        self.folder_edit.textEdited.connect(lambda _t: setattr(self, "_folder_user_set", True))
        row2.addWidget(self.folder_edit, 1)
        row2.addWidget(make_button("Examinar…", slot=self._browse, height=36))
        lay.addLayout(row2)

    def set_default_folder(self, folder):
        if not self._folder_user_set:
            self.folder_edit.setText(os.path.normpath(folder))

    def _browse(self):
        start = self.folder_edit.text().strip() or fm.documents_dir()
        d = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta de destino", start)
        if d:
            self.folder_edit.setText(os.path.normpath(d))
            self._folder_user_set = True

    def validate(self):
        """Devuelve un mensaje de error o None si todo está bien."""
        raw = self.name_edit.text().strip()
        clean = fm.sanitize_filename(raw)
        if clean.lower().endswith(".pdf"):
            clean = clean[:-4]
        if not raw or not clean.strip("._ "):
            return "Escribe un nombre válido para el archivo final."
        folder = self.folder_edit.text().strip()
        if not folder:
            return "Selecciona la carpeta donde se guardará el documento."
        if not os.path.isdir(folder):
            return "La carpeta de destino no existe. Selecciona otra carpeta."
        if not os.access(folder, os.W_OK):
            return "No tienes permiso para guardar en esa carpeta. Selecciona otra."
        return None

    def output_path(self):
        name = fm.ensure_extension(fm.sanitize_filename(self.name_edit.text().strip()), ".pdf")
        return os.path.join(self.folder_edit.text().strip(), name)


class ProgressPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)
        self.label = QLabel("")
        self.label.setObjectName("Hint")
        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        lay.addWidget(self.label)
        lay.addWidget(self.bar)
        self.hide()

    def start(self, message="Procesando…"):
        self.bar.setValue(0)
        self.label.setText(message)
        self.show()

    def update_progress(self, value, message=""):
        self.bar.setValue(int(value))
        if message:
            self.label.setText(message)

    def finish(self):
        self.hide()

"""Módulo 4: Organizar PDF de forma visual."""
from __future__ import annotations

import os

from PySide6.QtCore import Qt, QSize, QThread, Signal
from PySide6.QtGui import QIcon, QImage, QKeySequence, QPainter, QPixmap, QShortcut, QTransform
from PySide6.QtWidgets import (
    QFileDialog, QHBoxLayout, QLabel, QListWidgetItem, QMenu, QSlider, QVBoxLayout, QWidget,
)

from core.pdf_common import CORRUPT, NEEDS_PASSWORD, OK, WRONG_PASSWORD, PdfError, inspect_pdf, open_document
from core.pdf_organizer import PageSpec, render_page_thumbnail, save_organized
from ui import dialogs
from ui.widgets import PageGridWidget, ProgressPanel, make_button, move_selected_rows, page_header
from utils import file_manager as fm
from utils.workers import run_task

ROLE_SRC = int(Qt.ItemDataRole.UserRole)
ROLE_ROT = ROLE_SRC + 1
THUMB_W = 200          # ancho de miniatura (px) para documentos normales
THUMB_W_BIG = 140      # documentos de más de BIG_DOC páginas (ahorra memoria)
BIG_DOC = 300
OPERATION = "Organizar PDF"


class _ThumbLoader(QThread):
    """Genera las miniaturas en segundo plano para que la ventana no se congele."""

    thumb_ready = Signal(int, QImage)

    def __init__(self, path, password, count, width, parent=None):
        super().__init__(parent)
        self._path, self._password, self._count, self._width = path, password, count, width

    def run(self):
        try:
            doc = open_document(self._path, self._password)
        except PdfError:
            return
        try:
            for i in range(self._count):
                if self.isInterruptionRequested():
                    break
                try:
                    w, h, stride, data = render_page_thumbnail(doc, i, self._width)
                    img = QImage(data, w, h, stride, QImage.Format.Format_RGB888).copy()
                except Exception:  # noqa: BLE001
                    continue
                self.thumb_ready.emit(i, img)
        finally:
            doc.close()


class OrganizePdfPage(QWidget):
    def __init__(self, settings, history, parent=None):
        super().__init__(parent)
        self.settings, self.history = settings, history
        self._path = ""
        self._password = None
        self._page_count = 0
        self._dirty = False
        self._busy = False
        self._thumbs: dict[int, QPixmap] = {}
        self._loader = None
        self._worker = None
        self._pending_out = ""
        self._last_dir = ""
        self._placeholder = QPixmap(THUMB_W, int(THUMB_W * 1.414))
        self._placeholder.fill(Qt.GlobalColor.lightGray)

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 20)
        root.setSpacing(10)
        root.addWidget(page_header(
            "Organizar PDF",
            "Abre un PDF, arrastra las miniaturas para reordenar y usa los botones. "
            "El archivo original no se modifica: los cambios solo se aplican al guardar una copia."))

        top = QHBoxLayout()
        self.btn_open = make_button("📂  Abrir PDF", "primary", "Cargar un documento PDF", self._open_dialog, 42)
        self.btn_open.setStyleSheet("font-size: 10.5pt; padding: 8px 18px;")
        top.addWidget(self.btn_open)
        self.file_label = QLabel("Ningún documento cargado")
        self.file_label.setObjectName("Status")
        top.addWidget(self.file_label, 1)
        top.addWidget(QLabel("Tamaño:"))
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(90, 200)
        self.slider.setValue(150)
        self.slider.setFixedWidth(130)
        self.slider.valueChanged.connect(self._apply_size)
        top.addWidget(self.slider)
        root.addLayout(top)

        tools = QHBoxLayout()
        tools.setSpacing(6)
        self.btn_all = make_button("Seleccionar todo", slot=self._select_all, height=38)
        self.btn_first = make_button("⏮ Al inicio", slot=self._to_start, tooltip="Mover al principio", height=38)
        self.btn_left = make_button("◀ Izquierda", slot=self._left, tooltip="Mover a la izquierda", height=38)
        self.btn_right = make_button("Derecha ▶", slot=self._right, tooltip="Mover a la derecha", height=38)
        self.btn_last = make_button("Al final ⏭", slot=self._to_end, tooltip="Mover al final", height=38)
        self.btn_rotate = make_button("↻ Rotar", tooltip="Rotar las páginas seleccionadas", height=38)
        menu = QMenu(self.btn_rotate)
        for text, deg in (("↻  90° (derecha)", 90), ("🔄  180°", 180), ("↺  270° (izquierda)", 270)):
            menu.addAction(text, lambda _=False, d=deg: self._rotate(d))
        self.btn_rotate.setMenu(menu)
        self.btn_dup = make_button("⧉ Duplicar", slot=self._duplicate, tooltip="Duplicar las páginas seleccionadas", height=38)
        self.btn_del = make_button("🗑 Eliminar", "danger", "Eliminar las páginas seleccionadas (Supr)", self._delete, 38)
        for b in (self.btn_all, self.btn_first, self.btn_left, self.btn_right, self.btn_last,
                  self.btn_rotate, self.btn_dup, self.btn_del):
            tools.addWidget(b)
        tools.addStretch(1)
        root.addLayout(tools)

        self.grid = PageGridWidget("Arrastra aquí un archivo PDF\no pulsa «Abrir PDF»")
        self.grid.itemSelectionChanged.connect(self._update_status)
        self.grid.files_dropped.connect(self._on_dropped)
        self.grid.order_changed.connect(self._after_change)
        sc = QShortcut(QKeySequence(Qt.Key.Key_Delete), self.grid)
        sc.setContext(Qt.ShortcutContext.WidgetShortcut)
        sc.activated.connect(self._delete)
        root.addWidget(self.grid, 1)

        bottom = QHBoxLayout()
        self.status = QLabel("")
        self.status.setObjectName("Status")
        self.dirty_label = QLabel("")
        self.dirty_label.setObjectName("Dirty")
        bottom.addWidget(self.status)
        bottom.addWidget(self.dirty_label)
        bottom.addStretch(1)
        self.btn_restore = make_button("Restaurar original", slot=self._restore, tooltip="Descartar los cambios", height=44)
        self.btn_save = make_button("💾  GUARDAR PDF", "primary", "Guardar una copia con los cambios", self._save, 48)
        bottom.addWidget(self.btn_restore)
        bottom.addWidget(self.btn_save)
        root.addLayout(bottom)
        self.progress = ProgressPanel()
        root.addWidget(self.progress)

        self._lockables = [self.btn_open, self.btn_all, self.btn_first, self.btn_left, self.btn_right,
                           self.btn_last, self.btn_rotate, self.btn_dup, self.btn_del, self.btn_restore,
                           self.btn_save, self.grid]
        self._apply_size(self.slider.value())
        self._update_status()

    def apply_settings(self):
        pass

    # --- apariencia ----------------------------------------------------
    def _apply_size(self, value):
        self.grid.setIconSize(QSize(value, int(value * 1.4)))
        self.grid.setGridSize(QSize(value + 30, int(value * 1.4) + 58))

    def _update_status(self):
        n, sel = self.grid.count(), len(self.grid.selectedIndexes())
        self.status.setText(f"{n} página(s)  ·  {sel} seleccionada(s)" if n else "")
        self.dirty_label.setText("●  Cambios sin guardar" if self._dirty else "")

    # --- carga ---------------------------------------------------------
    def _open_dialog(self):
        start = self._last_dir or fm.documents_dir()
        path, _ = QFileDialog.getOpenFileName(self, "Abrir PDF", start, "Documentos PDF (*.pdf)")
        if path:
            self.load_pdf(path)

    def _on_dropped(self, paths):
        valid, rejected = fm.filter_by_extension(paths, (".pdf",))
        if not valid:
            dialogs.show_warning(self, "Solo se pueden abrir archivos PDF.")
            return
        if len(valid) > 1:
            dialogs.show_info(self, "Solo se puede organizar un PDF a la vez; se abrirá el primero.")
        self.load_pdf(valid[0])

    def load_pdf(self, path):
        if self._busy:
            return
        if not os.path.isfile(path) or not fm.has_extension(path, (".pdf",)):
            dialogs.show_warning(self, "Selecciona un archivo con extensión .pdf.")
            return
        if self._dirty and not dialogs.confirm(
                self, "Cambios sin guardar", "Tienes cambios sin guardar en el documento actual.\n¿Abrir otro PDF y descartarlos?",
                yes="Descartar y abrir"):
            return
        name = os.path.basename(path)
        password, info, attempts = None, inspect_pdf(path), 0
        while info.status in (NEEDS_PASSWORD, WRONG_PASSWORD) and attempts < 3:
            if info.status == WRONG_PASSWORD:
                dialogs.show_warning(self, "La contraseña no es correcta.")
            password = dialogs.ask_password(self, name)
            if password is None:
                return
            info = inspect_pdf(path, password)
            attempts += 1
        if info.status != OK:
            dialogs.show_error(self, f"No se pudo abrir «{name}».\n" + (
                "El archivo está dañado o no es un PDF válido." if info.status == CORRUPT
                else "La contraseña indicada no es correcta."))
            return
        self._last_dir = os.path.dirname(path)
        self._populate(path, password, info.pages)

    def _populate(self, path, password, pages):
        self._stop_loader()
        self._path, self._password, self._page_count = path, password, pages
        self._thumbs.clear()
        self.grid.clear()
        for i in range(pages):
            self.grid.addItem(self._make_item(i))
        self._dirty = False
        self._renumber()
        self.file_label.setText(f"📄 {os.path.basename(path)}  ·  {pages} página(s)")
        self.file_label.setToolTip(path)
        self._update_status()
        width = THUMB_W if pages <= BIG_DOC else THUMB_W_BIG
        self._loader = _ThumbLoader(path, password, pages, width, self)
        self._loader.thumb_ready.connect(self._on_thumb)
        self._loader.start()

    def _stop_loader(self):
        if self._loader is not None:
            try:
                self._loader.thumb_ready.disconnect(self._on_thumb)
            except (RuntimeError, TypeError):
                pass
            self._loader.requestInterruption()
            self._loader.wait(5000)
            self._loader = None

    def _on_thumb(self, index, image):
        pm = QPixmap.fromImage(image)
        painter = QPainter(pm)
        painter.setPen(Qt.GlobalColor.gray)
        painter.drawRect(0, 0, pm.width() - 1, pm.height() - 1)
        painter.end()
        self._thumbs[index] = pm
        for row in range(self.grid.count()):
            item = self.grid.item(row)
            if item.data(ROLE_SRC) == index:
                self._refresh_icon(item)

    # --- items ---------------------------------------------------------
    def _make_item(self, src, rot=0):
        item = QListWidgetItem()
        item.setData(ROLE_SRC, src)
        item.setData(ROLE_ROT, rot)
        item.setTextAlignment(Qt.AlignmentFlag.AlignHCenter)
        item.setToolTip(f"Página original {src + 1}")
        self._refresh_icon(item)
        return item

    def _refresh_icon(self, item):
        pm = self._thumbs.get(item.data(ROLE_SRC), self._placeholder)
        rot = item.data(ROLE_ROT) or 0
        if rot:
            pm = pm.transformed(QTransform().rotate(rot), Qt.TransformationMode.SmoothTransformation)
        item.setIcon(QIcon(pm))

    def _renumber(self):
        for row in range(self.grid.count()):
            item = self.grid.item(row)
            rot = item.data(ROLE_ROT) or 0
            item.setText(f"Página {row + 1}" + (f"\n↻ {rot}°" if rot else ""))

    def _after_change(self):
        self._dirty = True
        self._renumber()
        self._update_status()

    def _need_selection(self):
        if not self._path:
            dialogs.show_warning(self, "Primero abre un documento PDF.")
            return None
        rows = self.grid.selected_rows()
        if not rows:
            dialogs.show_warning(self, "Selecciona una o varias páginas (clic y Ctrl/Mayús para varias).")
            return None
        return rows

    # --- acciones ------------------------------------------------------
    def _select_all(self):
        if not self._path:
            dialogs.show_warning(self, "Primero abre un documento PDF.")
            return
        self.grid.selectAll()

    def _left(self):
        if self._need_selection() is not None and move_selected_rows(self.grid, -1):
            self._after_change()

    def _right(self):
        if self._need_selection() is not None and move_selected_rows(self.grid, +1):
            self._after_change()

    def _to_start(self):
        rows = self._need_selection()
        if rows is not None and rows != list(range(len(rows))):
            self.grid.move_rows_to(rows, 0)
            self._after_change()

    def _to_end(self):
        rows = self._need_selection()
        n = self.grid.count()
        if rows is not None and rows != list(range(n - len(rows), n)):
            self.grid.move_rows_to(rows, n)
            self._after_change()

    def _rotate(self, degrees):
        rows = self._need_selection()
        if rows is None:
            return
        for r in rows:
            item = self.grid.item(r)
            item.setData(ROLE_ROT, ((item.data(ROLE_ROT) or 0) + degrees) % 360)
            self._refresh_icon(item)
        self._after_change()

    def _duplicate(self):
        rows = self._need_selection()
        if rows is None:
            return
        for r in reversed(rows):
            src = self.grid.item(r)
            self.grid.insertItem(r + 1, self._make_item(src.data(ROLE_SRC), src.data(ROLE_ROT) or 0))
        self._after_change()

    def _delete(self):
        if self._busy:
            return
        rows = self._need_selection()
        if rows is None:
            return
        if len(rows) >= self.grid.count():
            dialogs.show_warning(self, "No puedes eliminar todas las páginas: el documento no puede quedar vacío.")
            return
        if not dialogs.confirm(self, "Eliminar páginas", f"¿Eliminar {len(rows)} página(s) seleccionada(s)?\n"
                               "El archivo original no se verá afectado.", yes="Eliminar"):
            return
        for r in reversed(rows):
            self.grid.takeItem(r)
        self._after_change()

    def _restore(self):
        if not self._path:
            dialogs.show_warning(self, "Primero abre un documento PDF.")
            return
        if self._dirty and not dialogs.confirm(self, "Restaurar original", "Se descartarán todos los cambios. ¿Continuar?",
                                               yes="Restaurar"):
            return
        self._populate(self._path, self._password, self._page_count)

    # --- guardado ------------------------------------------------------
    def _save(self):
        if self._busy:
            return
        if not self._path:
            dialogs.show_warning(self, "Primero abre un documento PDF.")
            return
        if self.grid.count() == 0:
            dialogs.show_warning(self, "El documento no tiene páginas para guardar.")
            return
        folder = self.settings.get("output_dir") or os.path.dirname(self._path)
        if not os.path.isdir(folder):
            folder = os.path.dirname(self._path)
        stem = os.path.splitext(os.path.basename(self._path))[0]
        default = os.path.join(folder, f"{stem}_organizado.pdf")
        out, _ = QFileDialog.getSaveFileName(self, "Guardar PDF organizado", default, "Documentos PDF (*.pdf)")
        if not out:
            return
        out = fm.ensure_extension(out, ".pdf")
        if fm.same_file(out, self._path):
            dialogs.show_error(self, "No se puede sobrescribir el archivo original.\n"
                                     "Guarda el resultado con otro nombre.")
            return
        specs = [PageSpec(self.grid.item(r).data(ROLE_SRC), self.grid.item(r).data(ROLE_ROT) or 0)
                 for r in range(self.grid.count())]
        src, pwd = self._path, self._password
        self._pending_out = out
        self._set_busy(True)
        self.progress.start("Guardando…")
        self._worker = run_task(self, lambda cb: save_organized(src, pwd, specs, out, cb),
                                self._on_progress, self._on_done, self._on_failed)

    def _set_busy(self, busy):
        self._busy = busy
        for w in self._lockables:
            w.setEnabled(not busy)

    def _on_progress(self, value, message):
        self.progress.update_progress(value, message)

    def _on_done(self, pages):
        self._set_busy(False)
        self.progress.finish()
        self._dirty = False
        self._update_status()
        self.history.add(OPERATION, self._pending_out)
        dialogs.show_success(self, f"Se guardó el PDF reorganizado ({pages} páginas).", self._pending_out)

    def _on_failed(self, message):
        self._set_busy(False)
        self.progress.finish()
        dialogs.show_error(self, message)

    # --- cierre --------------------------------------------------------
    def can_close(self):
        if self._dirty:
            return dialogs.confirm(self, "Cambios sin guardar",
                                   "Hay cambios sin guardar en «Organizar PDF».\n¿Salir de todos modos?", yes="Salir")
        return True

    def shutdown(self):
        self._stop_loader()

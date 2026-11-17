"""Módulo 1: Unir PDF."""
from __future__ import annotations

import os

from PySide6.QtWidgets import (
    QFileDialog, QHBoxLayout, QLabel, QListWidgetItem, QVBoxLayout, QWidget,
)

from core.pdf_common import CORRUPT, NEEDS_PASSWORD, OK, WRONG_PASSWORD, inspect_pdf
from core.pdf_merger import merge_pdfs
from ui import dialogs
from ui.widgets import (
    ROLE_PAGES, ROLE_PATH, ROLE_PWD, DropListWidget, OutputSelector, ProgressPanel,
    make_button, move_selected_rows, page_header,
)
from utils import file_manager as fm
from utils.workers import run_task

EXTENSIONS = (".pdf",)
OPERATION = "Unir PDF"


class MergePdfPage(QWidget):
    def __init__(self, settings, history, parent=None):
        super().__init__(parent)
        self.settings, self.history = settings, history
        self._busy = False
        self._worker = None
        self._pending_out = ""
        self._last_dir = ""

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 20)
        root.setSpacing(12)
        root.addWidget(page_header(
            "Unir PDF",
            "Agrega tus PDF, ordénalos arrastrándolos o con los botones y únelos en un solo documento.",
        ))

        body = QHBoxLayout()
        body.setSpacing(14)
        self.list = DropListWidget("Arrastra aquí tus archivos PDF\no pulsa «Agregar PDF»")
        self.list.model().rowsMoved.connect(self._update_summary)
        self.list.files_dropped.connect(self.add_files)
        body.addWidget(self.list, 1)

        side = QVBoxLayout()
        side.setSpacing(8)
        self.btn_add = make_button("➕  Agregar PDF", slot=self._pick_files)
        self.btn_up = make_button("⬆  Subir", None, "Mover hacia arriba", self._up)
        self.btn_down = make_button("⬇  Bajar", None, "Mover hacia abajo", self._down)
        self.btn_remove = make_button("🗑  Quitar", "danger", "Quitar los archivos seleccionados", self._remove)
        self.btn_clear = make_button("Limpiar lista", slot=self._clear)
        for b in (self.btn_add, self.btn_up, self.btn_down, self.btn_remove, self.btn_clear):
            b.setMinimumWidth(170)
            side.addWidget(b)
        side.addStretch(1)
        body.addLayout(side)
        root.addLayout(body, 1)

        self.summary = QLabel("")
        self.summary.setObjectName("Status")
        root.addWidget(self.summary)

        self.output = OutputSelector("PDF_unido")
        root.addWidget(self.output)

        self.progress = ProgressPanel()
        root.addWidget(self.progress)
        self.btn_merge = make_button("UNIR PDF", "primary", "Unir todos los archivos de la lista", self._merge, 48)
        root.addWidget(self.btn_merge)

        self._lockables = [self.list, self.btn_add, self.btn_up, self.btn_down, self.btn_remove,
                           self.btn_clear, self.output, self.btn_merge]
        self.apply_settings()
        self._update_summary()

    # --- configuración -------------------------------------------------
    def apply_settings(self):
        self.output.set_default_folder(self.settings.output_dir())

    # --- lista ---------------------------------------------------------
    def _pick_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Seleccionar archivos PDF", self._last_dir or fm.documents_dir(), "Documentos PDF (*.pdf)")
        if paths:
            self._last_dir = os.path.dirname(paths[0])
            self.add_files(paths)

    def add_files(self, paths):
        if self._busy:
            return
        valid, rejected = fm.filter_by_extension(paths, EXTENSIONS)
        errors = []
        for path in valid:
            name = os.path.basename(path)
            password = None
            info = inspect_pdf(path)
            attempts = 0
            while info.status in (NEEDS_PASSWORD, WRONG_PASSWORD) and attempts < 3:
                if info.status == WRONG_PASSWORD:
                    dialogs.show_warning(self, f"La contraseña de «{name}» no es correcta.")
                password = dialogs.ask_password(self, name)
                if password is None:
                    break
                info = inspect_pdf(path, password)
                attempts += 1
            if info.status == OK:
                item = QListWidgetItem(f"📄  {name}      ·      {info.pages} pág.")
                item.setToolTip(path)
                item.setData(ROLE_PATH, path)
                item.setData(ROLE_PWD, password)
                item.setData(ROLE_PAGES, info.pages)
                self.list.addItem(item)
            elif info.status == CORRUPT:
                errors.append(f"• {name}: está dañado o no es un PDF válido.")
            elif password is not None:
                errors.append(f"• {name}: contraseña incorrecta.")
        if rejected:
            errors += [f"• {os.path.basename(p) or p}: solo se permiten archivos .pdf." for p in rejected]
        if errors:
            dialogs.show_warning(self, "Algunos archivos no se agregaron:\n\n" + "\n".join(errors))
        self._update_summary()

    def _up(self):
        move_selected_rows(self.list, -1)

    def _down(self):
        move_selected_rows(self.list, +1)

    def _remove(self):
        rows = sorted((i.row() for i in self.list.selectedIndexes()), reverse=True)
        if not rows:
            dialogs.show_warning(self, "Selecciona primero los archivos que quieres quitar de la lista.")
            return
        for r in rows:
            self.list.takeItem(r)
        self._update_summary()

    def _clear(self):
        self.list.clear()
        self._update_summary()

    def _update_summary(self, *_args):
        n = self.list.count()
        pages = sum(int(self.list.item(i).data(ROLE_PAGES) or 0) for i in range(n))
        self.summary.setText(f"{n} archivo(s) en la lista  ·  {pages} página(s) en total" if n else
                             "Aún no hay archivos en la lista.")

    # --- proceso -------------------------------------------------------
    def _set_busy(self, busy):
        self._busy = busy
        for w in self._lockables:
            w.setEnabled(not busy)

    def _merge(self):
        if self._busy:
            return
        n = self.list.count()
        if n == 0:
            dialogs.show_warning(self, "No has seleccionado ningún archivo. Agrega al menos dos PDF para unirlos.")
            return
        if n == 1:
            dialogs.show_warning(self, "Agrega al menos un PDF más: se necesitan dos o más archivos para unirlos.")
            return
        err = self.output.validate()
        if err:
            dialogs.show_warning(self, err)
            return
        entries = [(self.list.item(i).data(ROLE_PATH), self.list.item(i).data(ROLE_PWD)) for i in range(n)]
        out = self.output.output_path()
        if any(fm.same_file(out, p) for p, _ in entries):
            dialogs.show_error(self, "El archivo de salida coincide con uno de los PDF originales.\n"
                                     "Elige otro nombre o carpeta para no sobrescribirlo.")
            return
        out = dialogs.resolve_overwrite(self, out)
        if out is None:
            return
        self._pending_out = out
        self._set_busy(True)
        self.progress.start("Preparando…")
        self._worker = run_task(self, lambda cb: merge_pdfs(entries, out, cb),
                                self._on_progress, self._on_done, self._on_failed)

    def _on_progress(self, value, message):
        self.progress.update_progress(value, message)

    def _on_done(self, pages):
        self._set_busy(False)
        self.progress.finish()
        self.history.add(OPERATION, self._pending_out)
        dialogs.show_success(self, f"Se unieron {self.list.count()} archivos ({pages} páginas).", self._pending_out)

    def _on_failed(self, message):
        self._set_busy(False)
        self.progress.finish()
        dialogs.show_error(self, message)

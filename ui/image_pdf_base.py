"""Pantalla base para convertir imágenes (JPG o PNG) a PDF."""
from __future__ import annotations

import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication, QColorDialog, QComboBox, QDoubleSpinBox, QFileDialog, QFormLayout, QFrame, QGroupBox,
    QHBoxLayout, QLabel, QListWidgetItem, QVBoxLayout, QWidget,
)

from core.image_converter import images_to_pdf
from ui import dialogs
from ui.widgets import (
    ROLE_PATH, DropListWidget, OutputSelector, ProgressPanel, make_button, move_selected_rows, page_header,
)
from utils import file_manager as fm
from utils.image_utils import load_preview
from utils.workers import run_task


class ImagePdfPage(QWidget):
    def __init__(self, kind, settings, history, parent=None):
        super().__init__(parent)
        self.kind, self.settings, self.history = kind, settings, history
        if kind == "png":
            self.exts, self.operation = (".png",), "PNG a PDF"
            self.file_filter, self.label = "Imágenes PNG (*.png)", "PNG"
        else:
            self.exts, self.operation = (".jpg", ".jpeg"), "JPG a PDF"
            self.file_filter, self.label = "Imágenes JPG (*.jpg *.jpeg)", "JPG"
        self._busy = False
        self._worker = None
        self._pending_out = ""
        self._last_dir = ""
        self._bg_hex = "#FFFFFF"
        self._build_ui()
        self.apply_settings()

    # --- interfaz ------------------------------------------------------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 20)
        root.setSpacing(12)
        extra = " Las imágenes PNG con transparencia se colocan sobre el color de fondo elegido." if self.kind == "png" else ""
        root.addWidget(page_header(
            f"{self.label} a PDF",
            f"Agrega imágenes {self.label}, ordénalas y conviértelas en un único PDF sin deformarlas.{extra}"))

        body = QHBoxLayout()
        body.setSpacing(16)

        left = QVBoxLayout()
        self.list = DropListWidget(f"Arrastra aquí tus imágenes {self.label}\no pulsa «Agregar imágenes»", icon_size=64)
        self.list.currentItemChanged.connect(self._on_current_changed)
        self.list.files_dropped.connect(self.add_files)
        left.addWidget(self.list, 1)
        row = QHBoxLayout()
        self.btn_add = make_button("➕  Agregar imágenes", slot=self._pick_files)
        self.btn_up = make_button("⬆", "", "Subir", self._up)
        self.btn_down = make_button("⬇", "", "Bajar", self._down)
        self.btn_remove = make_button("🗑  Quitar", "danger", "Quitar las imágenes seleccionadas", self._remove)
        self.btn_clear = make_button("Limpiar", slot=self._clear)
        for b in (self.btn_up, self.btn_down):
            b.setFixedWidth(48)
        for b in (self.btn_add, self.btn_up, self.btn_down, self.btn_remove, self.btn_clear):
            row.addWidget(b)
        left.addLayout(row)
        self.summary = QLabel("")
        self.summary.setObjectName("Status")
        left.addWidget(self.summary)
        body.addLayout(left, 1)

        right = QVBoxLayout()
        right.setSpacing(10)
        right_w = QWidget()
        right_w.setFixedWidth(350)
        right_w.setLayout(right)
        right.setContentsMargins(0, 0, 0, 0)

        self.preview = QLabel("Selecciona una imagen\npara ver su vista previa")
        self.preview.setObjectName("Preview")
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setFixedSize(350, 230)
        right.addWidget(self.preview)

        group = QGroupBox("Opciones de página")
        form = QFormLayout(group)
        form.setVerticalSpacing(8)
        self.size_combo = QComboBox()
        for text, data in (("A4", "A4"), ("Carta", "LETTER"), ("Tamaño original", "ORIGINAL")):
            self.size_combo.addItem(text, data)
        self.orient_combo = QComboBox()
        for text, data in (("Vertical", "vertical"), ("Horizontal", "horizontal"), ("Automática (según la imagen)", "auto")):
            self.orient_combo.addItem(text, data)
        self.margin_spin = QDoubleSpinBox()
        self.margin_spin.setRange(0, 50)
        self.margin_spin.setDecimals(0)
        self.margin_spin.setValue(5)
        self.margin_spin.setSuffix(" mm")
        form.addRow("Tamaño:", self.size_combo)
        form.addRow("Orientación:", self.orient_combo)
        form.addRow("Margen:", self.margin_spin)
        if self.kind == "png":
            bg_row = QHBoxLayout()
            self.swatch = QFrame()
            self.swatch.setFixedSize(28, 28)
            bg_row.addWidget(self.swatch)
            bg_row.addWidget(make_button("Elegir color…", slot=self._pick_color, height=34))
            bg_row.addWidget(make_button("Blanco", slot=self._white_bg, height=34))
            bg_row.addStretch(1)
            form.addRow("Fondo:", bg_row)
        self.size_combo.currentIndexChanged.connect(self._update_option_states)
        right.addWidget(group)

        self.output = OutputSelector(f"{self.label}_a_PDF")
        right.addWidget(self.output)
        right.addStretch(1)
        self.progress = ProgressPanel()
        right.addWidget(self.progress)
        self.btn_convert = make_button("CONVERTIR A PDF", "primary", "Crear el PDF con todas las imágenes", self._convert, 48)
        right.addWidget(self.btn_convert)
        body.addWidget(right_w)
        root.addLayout(body, 1)

        self._lockables = [self.list, self.btn_add, self.btn_up, self.btn_down, self.btn_remove, self.btn_clear,
                           self.size_combo, self.orient_combo, self.margin_spin, self.output, self.btn_convert]
        self._update_summary()

    # --- configuración -------------------------------------------------
    @staticmethod
    def _set_combo(combo, data):
        idx = combo.findData(data)
        if idx >= 0:
            combo.setCurrentIndex(idx)

    def apply_settings(self):
        self.output.set_default_folder(self.settings.output_dir())
        self._set_combo(self.size_combo, self.settings.get("page_size"))
        self._set_combo(self.orient_combo, self.settings.get("orientation"))
        if self.kind == "png":
            self._set_bg(self.settings.get("png_background") or "#FFFFFF")
        self._update_option_states()

    def _update_option_states(self):
        original = self.size_combo.currentData() == "ORIGINAL"
        self.orient_combo.setEnabled(not original and not self._busy)
        self.margin_spin.setEnabled(not original and not self._busy)

    def _bg_rgb(self):
        c = QColor(self._bg_hex)
        return (c.red(), c.green(), c.blue())

    def _set_bg(self, hex_color):
        self._bg_hex = hex_color
        self.swatch.setStyleSheet(f"background: {hex_color}; border: 1px solid #9CA3AF; border-radius: 6px;")
        self._show_preview(self.list.currentItem())

    def _pick_color(self):
        color = QColorDialog.getColor(QColor(self._bg_hex), self, "Color de fondo del PDF")
        if color.isValid():
            self._set_bg(color.name())

    def _white_bg(self):
        self._set_bg("#FFFFFF")

    # --- lista ---------------------------------------------------------
    def _pick_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, f"Seleccionar imágenes {self.label}", self._last_dir or fm.documents_dir(), self.file_filter)
        if paths:
            self._last_dir = os.path.dirname(paths[0])
            self.add_files(paths)

    def add_files(self, paths):
        if self._busy:
            return
        valid, rejected = fm.filter_by_extension(paths, self.exts)
        errors = [f"• {os.path.basename(p) or p}: formato no permitido (solo {', '.join(self.exts)})." for p in rejected]
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            for path in valid:
                img = load_preview(path, 96)
                if img is None:
                    errors.append(f"• {os.path.basename(path)}: no se pudo abrir (archivo dañado).")
                    continue
                item = QListWidgetItem(QIcon(QPixmap.fromImage(img)), os.path.basename(path))
                item.setToolTip(path)
                item.setData(ROLE_PATH, path)
                self.list.addItem(item)
        finally:
            QApplication.restoreOverrideCursor()
        if errors:
            dialogs.show_warning(self, "Algunos archivos no se agregaron:\n\n" + "\n".join(errors))
        if self.list.currentItem() is None and self.list.count():
            self.list.setCurrentRow(0)
        self._update_summary()

    def _on_current_changed(self, current, _previous):
        self._show_preview(current)

    def _show_preview(self, item):
        if item is None:
            self.preview.setPixmap(QPixmap())
            self.preview.setText("Selecciona una imagen\npara ver su vista previa")
            return
        bg = self._bg_rgb() if self.kind == "png" else None
        img = load_preview(item.data(ROLE_PATH), 700, bg)
        if img is None:
            self.preview.setPixmap(QPixmap())
            self.preview.setText("No se pudo mostrar la imagen")
            return
        pm = QPixmap.fromImage(img).scaled(self.preview.width() - 12, self.preview.height() - 12,
                                           Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.preview.setPixmap(pm)

    def _up(self):
        move_selected_rows(self.list, -1)

    def _down(self):
        move_selected_rows(self.list, +1)

    def _remove(self):
        rows = sorted((i.row() for i in self.list.selectedIndexes()), reverse=True)
        if not rows:
            dialogs.show_warning(self, "Selecciona primero las imágenes que quieres quitar.")
            return
        for r in rows:
            self.list.takeItem(r)
        self._update_summary()

    def _clear(self):
        self.list.clear()
        self._update_summary()

    def _update_summary(self):
        n = self.list.count()
        self.summary.setText(f"{n} imagen(es) en la lista  ·  cada una será una página del PDF" if n
                             else "Aún no hay imágenes en la lista.")

    # --- proceso -------------------------------------------------------
    def _set_busy(self, busy):
        self._busy = busy
        for w in self._lockables:
            w.setEnabled(not busy)
        if not busy:
            self._update_option_states()

    def _convert(self):
        if self._busy:
            return
        n = self.list.count()
        if n == 0:
            dialogs.show_warning(self, "No has seleccionado ninguna imagen. Agrega al menos una para convertirla.")
            return
        err = self.output.validate()
        if err:
            dialogs.show_warning(self, err)
            return
        paths = [self.list.item(i).data(ROLE_PATH) for i in range(n)]
        missing = [os.path.basename(p) for p in paths if not os.path.isfile(p)]
        if missing:
            dialogs.show_error(self, "Estos archivos ya no existen:\n" + "\n".join(missing))
            return
        out = dialogs.resolve_overwrite(self, self.output.output_path())
        if out is None:
            return
        size, orient, margin = self.size_combo.currentData(), self.orient_combo.currentData(), self.margin_spin.value()
        bg = self._bg_rgb() if self.kind == "png" else (255, 255, 255)
        self._pending_out = out
        self._set_busy(True)
        self.progress.start("Preparando…")
        self._worker = run_task(
            self, lambda cb: images_to_pdf(paths, out, size, orient, margin, bg, cb),
            self._on_progress, self._on_done, self._on_failed)

    def _on_progress(self, value, message):
        self.progress.update_progress(value, message)

    def _on_done(self, pages):
        self._set_busy(False)
        self.progress.finish()
        self.history.add(self.operation, self._pending_out)
        dialogs.show_success(self, f"Se creó el PDF con {pages} página(s).", self._pending_out)

    def _on_failed(self, message):
        self._set_busy(False)
        self.progress.finish()
        dialogs.show_error(self, message)

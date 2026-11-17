"""Ventana principal con menú lateral."""
from __future__ import annotations

import os

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QButtonGroup, QFrame, QLabel, QMainWindow, QPushButton, QStackedWidget, QVBoxLayout, QHBoxLayout, QWidget,
)

from ui.history import HistoryPage
from ui.home import HomePage
from ui.jpg_to_pdf import JpgToPdfPage
from ui.merge_pdf import MergePdfPage
from ui.organize_pdf import OrganizePdfPage
from ui.png_to_pdf import PngToPdfPage
from ui.settings import SettingsPage
from utils.file_manager import resource_path
from utils.workers import wait_all_tasks

PAGE_HOME, PAGE_MERGE, PAGE_JPG, PAGE_PNG, PAGE_ORGANIZE, PAGE_HISTORY, PAGE_SETTINGS = range(7)

NAV_ITEMS = (
    ("🏠   Inicio", PAGE_HOME),
    ("🔗   Unir PDF", PAGE_MERGE),
    ("🖼   JPG a PDF", PAGE_JPG),
    ("🖼   PNG a PDF", PAGE_PNG),
    ("📑   Organizar PDF", PAGE_ORGANIZE),
    ("🕘   Historial de archivos", PAGE_HISTORY),
    ("⚙   Configuración", PAGE_SETTINGS),
)


class MainWindow(QMainWindow):
    def __init__(self, settings, history):
        super().__init__()
        self.settings, self.history = settings, history
        self.setWindowTitle("PDF MASTER")
        self.resize(1240, 800)
        self.setMinimumSize(1020, 680)
        icon = resource_path("assets/icons/app.png")
        if os.path.exists(icon):
            self.setWindowIcon(QIcon(icon))

        central = QWidget()
        central.setObjectName("Content")
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._build_sidebar())

        self.stack = QStackedWidget()
        layout.addWidget(self.stack, 1)
        self.setCentralWidget(central)

        self.home = HomePage([
            ("🔗  Unir PDF", "Combina varios documentos en uno solo", PAGE_MERGE),
            ("🖼  JPG a PDF", "Convierte fotos JPG/JPEG en un PDF", PAGE_JPG),
            ("🖼  PNG a PDF", "Convierte PNG (con transparencia) a PDF", PAGE_PNG),
            ("📑  Organizar PDF", "Reordena, rota, duplica y elimina páginas", PAGE_ORGANIZE),
        ])
        self.home.navigate.connect(self.go)
        self.merge_page = MergePdfPage(settings, history)
        self.jpg_page = JpgToPdfPage(settings, history)
        self.png_page = PngToPdfPage(settings, history)
        self.organize_page = OrganizePdfPage(settings, history)
        self.history_page = HistoryPage(history)
        self.settings_page = SettingsPage(settings)
        self.settings_page.saved.connect(self._on_settings_saved)
        for page in (self.home, self.merge_page, self.jpg_page, self.png_page,
                     self.organize_page, self.history_page, self.settings_page):
            self.stack.addWidget(page)

        self.statusBar().setSizeGripEnabled(False)
        self.statusBar().showMessage("Listo  ·  Todo se procesa localmente en tu equipo")
        self.go(PAGE_HOME)

    def _build_sidebar(self):
        side = QFrame()
        side.setObjectName("Sidebar")
        side.setFixedWidth(240)
        lay = QVBoxLayout(side)
        lay.setContentsMargins(16, 22, 16, 16)
        lay.setSpacing(4)
        logo = QLabel("PDF MASTER")
        logo.setObjectName("Logo")
        sub = QLabel("Gestor de PDF e imágenes")
        sub.setObjectName("LogoSub")
        lay.addWidget(logo)
        lay.addWidget(sub)
        lay.addSpacing(18)
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        self.nav_buttons = {}
        for text, index in NAV_ITEMS:
            btn = QPushButton(text)
            btn.setObjectName("NavButton")
            btn.setCheckable(True)
            btn.setMinimumHeight(44)
            btn.clicked.connect(lambda _=False, i=index: self.go(i))
            self.nav_group.addButton(btn)
            self.nav_buttons[index] = btn
            lay.addWidget(btn)
        lay.addStretch(1)
        footer = QLabel("🔒 100% local\nTus archivos no salen de tu equipo")
        footer.setObjectName("SidebarFooter")
        lay.addWidget(footer)
        return side

    def go(self, index):
        self.stack.setCurrentIndex(index)
        self.nav_buttons[index].setChecked(True)
        if index == PAGE_HISTORY:
            self.history_page.refresh()

    def _on_settings_saved(self):
        self.history.set_limit(int(self.settings.get("history_limit") or 100))
        for page in (self.merge_page, self.jpg_page, self.png_page, self.organize_page):
            page.apply_settings()

    def closeEvent(self, event):
        if not self.organize_page.can_close():
            event.ignore()
            return
        self.organize_page.shutdown()
        wait_all_tasks()
        event.accept()

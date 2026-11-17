"""PDF MASTER - punto de entrada de la aplicación."""
import sys

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from core.history_manager import HistoryManager
from core.settings_manager import SettingsManager
from ui.main_window import MainWindow
from ui.styles import STYLESHEET


def main():
    if sys.platform.startswith("win"):
        try:  # icono propio en la barra de tareas de Windows
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("pdfmaster.app")
        except Exception:  # noqa: BLE001
            pass
    app = QApplication(sys.argv)
    app.setApplicationName("PDF MASTER")
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))
    app.setStyleSheet(STYLESHEET)

    settings = SettingsManager()
    history = HistoryManager(settings.get("history_limit"))
    window = MainWindow(settings, history)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

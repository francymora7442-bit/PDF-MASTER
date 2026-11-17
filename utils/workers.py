"""Ejecución de tareas largas en segundo plano para no congelar la interfaz."""
from __future__ import annotations

from PySide6.QtCore import QThread, Signal

_ACTIVE: set = set()


class TaskWorker(QThread):
    progress = Signal(int, str)
    succeeded = Signal(object)
    failed = Signal(str)

    def __init__(self, func, parent=None):
        super().__init__(parent)
        self._func = func

    def run(self):
        try:
            result = self._func(lambda p, m="": self.progress.emit(int(p), str(m)))
        except Exception as exc:  # noqa: BLE001 - se muestra el mensaje al usuario
            self.failed.emit(str(exc) or exc.__class__.__name__)
        else:
            self.succeeded.emit(result)


def run_task(parent, func, on_progress, on_success, on_error) -> TaskWorker:
    """Lanza func(progress_cb) en un hilo. Los callbacks deben ser métodos de un QObject."""
    worker = TaskWorker(func)
    worker.progress.connect(on_progress)
    worker.succeeded.connect(on_success)
    worker.failed.connect(on_error)
    _ACTIVE.add(worker)
    worker.finished.connect(lambda w=worker: _ACTIVE.discard(w))
    worker.start()
    return worker


def wait_all_tasks(timeout_ms: int = 10000):
    for w in list(_ACTIVE):
        w.wait(timeout_ms)

"""Mensajes y diálogos reutilizables."""
from __future__ import annotations

import os

from PySide6.QtWidgets import QInputDialog, QLineEdit, QMessageBox

from utils import file_manager as fm


def _box(parent, icon, title, text):
    box = QMessageBox(parent)
    box.setIcon(icon)
    box.setWindowTitle(title)
    box.setText(text)
    return box


def show_info(parent, text, title="PDF MASTER"):
    box = _box(parent, QMessageBox.Icon.Information, title, text)
    box.addButton("Aceptar", QMessageBox.ButtonRole.AcceptRole)
    box.exec()


def show_warning(parent, text, title="Atención"):
    box = _box(parent, QMessageBox.Icon.Warning, title, text)
    box.addButton("Aceptar", QMessageBox.ButtonRole.AcceptRole)
    box.exec()


def show_error(parent, text, title="Ocurrió un problema", details=None):
    box = _box(parent, QMessageBox.Icon.Critical, title, text)
    if details:
        box.setDetailedText(details)
    box.addButton("Aceptar", QMessageBox.ButtonRole.AcceptRole)
    box.exec()


def show_success(parent, text, path=None):
    box = _box(parent, QMessageBox.Icon.Information, "Operación completada", "✔ " + text)
    open_btn = None
    if path:
        box.setInformativeText(f"Archivo guardado en:\n{path}")
        open_btn = box.addButton("Abrir carpeta", QMessageBox.ButtonRole.ActionRole)
    box.addButton("Aceptar", QMessageBox.ButtonRole.AcceptRole)
    box.exec()
    if open_btn is not None and box.clickedButton() is open_btn:
        fm.open_folder(path)


def confirm(parent, title, text, yes="Sí", no="Cancelar") -> bool:
    box = _box(parent, QMessageBox.Icon.Question, title, text)
    yes_btn = box.addButton(yes, QMessageBox.ButtonRole.AcceptRole)
    no_btn = box.addButton(no, QMessageBox.ButtonRole.RejectRole)
    box.setDefaultButton(no_btn)
    box.exec()
    return box.clickedButton() is yes_btn


def ask_password(parent, filename):
    text, ok = QInputDialog.getText(
        parent,
        "PDF protegido",
        f"«{filename}» está protegido con contraseña.\nEscribe la contraseña para abrirlo:",
        QLineEdit.EchoMode.Password,
    )
    return text if ok and text else None


def resolve_overwrite(parent, path):
    """Si el archivo existe pregunta qué hacer. Devuelve la ruta final o None si se cancela."""
    if not os.path.exists(path):
        return path
    box = _box(parent, QMessageBox.Icon.Warning, "El archivo ya existe",
               f"Ya existe un archivo llamado «{os.path.basename(path)}» en esa carpeta.")
    box.setInformativeText("¿Qué deseas hacer?")
    replace = box.addButton("Reemplazar", QMessageBox.ButtonRole.DestructiveRole)
    keep = box.addButton("Guardar con otro nombre", QMessageBox.ButtonRole.AcceptRole)
    box.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
    box.setDefaultButton(keep)
    box.exec()
    clicked = box.clickedButton()
    if clicked is replace:
        return path
    if clicked is keep:
        return fm.unique_path(path)
    return None

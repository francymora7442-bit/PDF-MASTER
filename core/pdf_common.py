"""Funciones comunes de PDF: apertura segura y guardado atómico."""
from __future__ import annotations

import os
from dataclasses import dataclass

try:
    import pymupdf as fitz
except ImportError:  # versiones antiguas de PyMuPDF
    import fitz  # type: ignore

OK = "ok"
NEEDS_PASSWORD = "needs_password"
WRONG_PASSWORD = "wrong_password"
CORRUPT = "corrupt"


class PdfError(Exception):
    """Error con un mensaje claro para mostrar al usuario."""


@dataclass
class PdfInfo:
    status: str
    pages: int = 0


def inspect_pdf(path: str, password: str | None = None) -> PdfInfo:
    try:
        doc = fitz.open(path, filetype="pdf")
    except Exception:  # noqa: BLE001
        return PdfInfo(CORRUPT)
    try:
        if doc.needs_pass:
            if not password:
                return PdfInfo(NEEDS_PASSWORD)
            if not doc.authenticate(password):
                return PdfInfo(WRONG_PASSWORD)
        pages = doc.page_count
        return PdfInfo(OK if pages > 0 else CORRUPT, pages)
    except Exception:  # noqa: BLE001
        return PdfInfo(CORRUPT)
    finally:
        doc.close()


def open_document(path: str, password: str | None = None):
    name = os.path.basename(path)
    try:
        doc = fitz.open(path, filetype="pdf")
    except Exception as exc:  # noqa: BLE001
        raise PdfError(f"«{name}» está dañado o no es un PDF válido.") from exc
    if doc.needs_pass and (not password or not doc.authenticate(password)):
        doc.close()
        raise PdfError(f"«{name}» está protegido con contraseña y no se pudo abrir.")
    if doc.page_count == 0:
        doc.close()
        raise PdfError(f"«{name}» no contiene páginas.")
    return doc


def save_document(doc, output_path: str, garbage: int = 3) -> None:
    """Guarda en un archivo temporal y lo renombra al final: nunca deja archivos a medias."""
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    tmp = output_path + ".tmp"
    try:
        doc.save(tmp, garbage=garbage, deflate=True)
        os.replace(tmp, output_path)
    except Exception as exc:  # noqa: BLE001
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass
        raise PdfError(
            f"No se pudo guardar el archivo. Comprueba que no esté abierto en otro programa "
            f"y que tengas permiso de escritura.\n\nDetalle: {exc}"
        ) from exc

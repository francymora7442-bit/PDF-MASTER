"""Unión de varios PDF en un único documento."""
from __future__ import annotations

import os

from .pdf_common import PdfError, fitz, open_document, save_document


def merge_pdfs(entries, output_path: str, progress=None) -> int:
    """entries: lista de (ruta, contraseña|None) en el orden final. Devuelve el total de páginas."""
    if not entries:
        raise PdfError("No hay archivos para unir.")
    total = len(entries)
    out = fitz.open()
    try:
        for i, (path, password) in enumerate(entries):
            name = os.path.basename(path)
            if progress:
                progress(int(i / total * 90), f"Agregando «{name}»…")
            src = open_document(path, password)
            try:
                out.insert_pdf(src)
            except Exception as exc:  # noqa: BLE001
                raise PdfError(f"No se pudo agregar «{name}»: {exc}") from exc
            finally:
                src.close()
        pages = out.page_count
        if progress:
            progress(93, "Guardando documento…")
        save_document(out, output_path, garbage=3)
    finally:
        out.close()
    if progress:
        progress(100, "Listo")
    return pages

"""Reorganización de páginas de un PDF (el original nunca se modifica)."""
from __future__ import annotations

from dataclasses import dataclass

from .pdf_common import PdfError, fitz, open_document, save_document


@dataclass
class PageSpec:
    source_index: int      # página del PDF original (0 = primera)
    rotation: int = 0      # rotación adicional en grados (0, 90, 180, 270)


def render_page_thumbnail(doc, index: int, width: int = 260):
    """Devuelve (ancho, alto, stride, bytes RGB) de la miniatura de una página."""
    page = doc[index]
    rect = page.rect
    zoom = width / rect.width if rect.width else 1.0
    zoom = max(0.05, min(zoom, 4.0))
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
    return pix.width, pix.height, pix.stride, bytes(pix.samples)


def save_organized(src_path: str, password, specs, output_path: str, progress=None) -> int:
    """Crea un PDF nuevo con las páginas en el orden/rotación indicados."""
    if not specs:
        raise PdfError("El documento no puede quedar sin páginas.")
    src = open_document(src_path, password)
    out = fitz.open()
    try:
        n = src.page_count
        for s in specs:
            if not 0 <= s.source_index < n:
                raise PdfError("Índice de página no válido.")
        # Agrupa páginas consecutivas para insertar por bloques (más rápido).
        runs: list[list[int]] = []
        for s in specs:
            if runs and s.source_index == runs[-1][1] + 1:
                runs[-1][1] = s.source_index
            else:
                runs.append([s.source_index, s.source_index])
        total, done = len(specs), 0
        for a, b in runs:
            out.insert_pdf(src, from_page=a, to_page=b)
            done += b - a + 1
            if progress:
                progress(int(done / total * 80), f"Procesando página {done} de {total}…")
        for i, s in enumerate(specs):
            if s.rotation % 360:
                page = out[i]
                page.set_rotation((page.rotation + s.rotation) % 360)
        try:
            meta = {k: v for k, v in (src.metadata or {}).items() if v}
            if meta:
                out.set_metadata(meta)
        except Exception:  # noqa: BLE001
            pass
        if progress:
            progress(88, "Guardando documento…")
        save_document(out, output_path, garbage=4)
    finally:
        out.close()
        src.close()
    if progress:
        progress(100, "Listo")
    return len(specs)

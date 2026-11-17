"""Conversión de imágenes JPG/PNG a PDF sin deformar ni recortar."""
from __future__ import annotations

import io
import os
from dataclasses import dataclass

from PIL import Image, ImageOps

from .pdf_common import PdfError, fitz, save_document

Image.MAX_IMAGE_PIXELS = None

MM_TO_PT = 72 / 25.4
PAGE_SIZES = {"A4": (595.276, 841.890), "LETTER": (612.0, 792.0)}
MAX_PAGE_PT = 14400  # límite de tamaño de página de un PDF (200 pulgadas)


@dataclass
class _Prepared:
    width: int
    height: int
    dpi: float
    filename: str | None = None
    stream: bytes | None = None


def _prepare(path: str) -> _Prepared:
    """Lee la imagen. Si es JPG/PNG estándar se incrusta tal cual (sin pérdida de calidad)."""
    name = os.path.basename(path)
    try:
        with Image.open(path) as im:
            fmt, mode = im.format, im.mode
            dpi = 96.0
            raw_dpi = im.info.get("dpi")
            if raw_dpi:
                try:
                    candidate = float(raw_dpi[0])
                    if 30 <= candidate <= 1200:
                        dpi = candidate
                except (TypeError, ValueError):
                    pass
            exif = im.getexif()
            orientation = exif.get(274, 1) if exif else 1
            if fmt in ("JPEG", "PNG") and mode in ("RGB", "L", "RGBA") and orientation in (0, 1, None):
                return _Prepared(im.width, im.height, dpi, filename=path)
            im.load()
            fixed = ImageOps.exif_transpose(im)
            has_alpha = (
                fixed.mode in ("RGBA", "LA", "PA")
                or "transparency" in fixed.info
                or "transparency" in im.info
            )
            buf = io.BytesIO()
            if has_alpha:
                fixed.convert("RGBA").save(buf, format="PNG")
            elif fmt in ("JPEG", "MPO"):
                fixed.convert("RGB").save(buf, format="JPEG", quality=95, subsampling=0)
            else:
                fixed.convert("RGB").save(buf, format="PNG")
            return _Prepared(fixed.width, fixed.height, dpi, stream=buf.getvalue())
    except Exception as exc:  # noqa: BLE001
        raise PdfError(f"No se pudo leer la imagen «{name}»: {exc}") from exc


def images_to_pdf(
    image_paths,
    output_path: str,
    page_size: str = "A4",
    orientation: str = "vertical",
    margin_mm: float = 5.0,
    background=(255, 255, 255),
    progress=None,
) -> int:
    """Crea un PDF con una imagen por página. Devuelve el número de páginas."""
    if not image_paths:
        raise PdfError("No hay imágenes para convertir.")
    page_size = page_size.upper()
    if page_size not in PAGE_SIZES and page_size != "ORIGINAL":
        raise PdfError(f"Tamaño de página no válido: {page_size}")
    fill = tuple(c / 255 for c in background)
    total = len(image_paths)
    doc = fitz.open()
    try:
        for i, path in enumerate(image_paths):
            if progress:
                progress(int(i / total * 90), f"Procesando imagen {i + 1} de {total}…")
            img = _prepare(path)
            if page_size == "ORIGINAL":
                pw, ph = img.width * 72 / img.dpi, img.height * 72 / img.dpi
                shrink = min(1.0, MAX_PAGE_PT / pw, MAX_PAGE_PT / ph)
                pw, ph = max(pw * shrink, 10), max(ph * shrink, 10)
                margin = 0.0
            else:
                bw, bh = PAGE_SIZES[page_size]
                if orientation == "auto":
                    landscape = img.width > img.height
                else:
                    landscape = orientation == "horizontal"
                pw, ph = (bh, bw) if landscape else (bw, bh)
                margin = min(max(0.0, margin_mm) * MM_TO_PT, min(pw, ph) / 4)
            page = doc.new_page(width=pw, height=ph)
            page.draw_rect(page.rect, color=None, fill=fill, width=0)
            scale = min((pw - 2 * margin) / img.width, (ph - 2 * margin) / img.height)
            w, h = img.width * scale, img.height * scale
            x0, y0 = (pw - w) / 2, (ph - h) / 2
            rect = fitz.Rect(x0, y0, x0 + w, y0 + h)
            if img.stream is not None:
                page.insert_image(rect, stream=img.stream, keep_proportion=False)
            else:
                page.insert_image(rect, filename=img.filename, keep_proportion=False)
        pages = doc.page_count
        if progress:
            progress(93, "Guardando PDF…")
        save_document(doc, output_path, garbage=3)
    finally:
        doc.close()
    if progress:
        progress(100, "Listo")
    return pages

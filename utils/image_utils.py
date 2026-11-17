"""Carga de imágenes para vistas previas."""
from __future__ import annotations

from PIL import Image, ImageOps
from PySide6.QtGui import QImage

Image.MAX_IMAGE_PIXELS = None  # archivos locales: no bloquear escaneos grandes


def pil_to_qimage(im: Image.Image) -> QImage:
    im = im.convert("RGBA")
    w, h = im.size
    data = im.tobytes("raw", "RGBA")
    return QImage(data, w, h, 4 * w, QImage.Format.Format_RGBA8888).copy()


def load_preview(path: str, max_side: int, background=None):
    """Devuelve un QImage reducido (respetando la orientación EXIF) o None si falla."""
    try:
        with Image.open(path) as im:
            try:
                im.draft("RGB", (max_side * 2, max_side * 2))  # acelera JPG grandes
            except Exception:  # noqa: BLE001
                pass
            im = ImageOps.exif_transpose(im)
            im.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
            im = im.convert("RGBA")
            if background is not None:
                base = Image.new("RGBA", im.size, tuple(background) + (255,))
                im = Image.alpha_composite(base, im)
            return pil_to_qimage(im)
    except Exception:  # noqa: BLE001
        return None

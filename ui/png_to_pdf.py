"""Módulo 3: PNG a PDF (con soporte de transparencia y color de fondo)."""
from ui.image_pdf_base import ImagePdfPage


class PngToPdfPage(ImagePdfPage):
    def __init__(self, settings, history, parent=None):
        super().__init__("png", settings, history, parent)

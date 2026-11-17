"""Módulo 2: JPG a PDF."""
from ui.image_pdf_base import ImagePdfPage


class JpgToPdfPage(ImagePdfPage):
    def __init__(self, settings, history, parent=None):
        super().__init__("jpg", settings, history, parent)

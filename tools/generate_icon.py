"""Genera assets/icons/app.png y app.ico (ejecutar solo si quieres regenerar el icono)."""
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent.parent / "assets" / "icons"
OUT.mkdir(parents=True, exist_ok=True)
S = 1024
img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
d.rounded_rectangle((40, 40, S - 40, S - 40), radius=210, fill=(37, 99, 235, 255))
d.polygon([(290, 190), (620, 190), (760, 330), (760, 830), (290, 830)], fill=(255, 255, 255, 255))
d.polygon([(620, 190), (760, 330), (620, 330)], fill=(191, 219, 254, 255))
for i, w in enumerate((340, 340, 340, 220)):
    y = 430 + i * 85
    d.rounded_rectangle((350, y, 350 + w, y + 36), radius=18, fill=(147, 197, 253, 255))
d.rounded_rectangle((350, 700, 560, 780), radius=20, fill=(37, 99, 235, 255))
img.resize((256, 256), Image.Resampling.LANCZOS).save(OUT / "app.png")
img.save(OUT / "app.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print("Iconos generados en", OUT)

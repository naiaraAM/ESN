import os
import sys
from PIL import Image  # type: ignore

def get_watermark_path():
    """Obtiene la ruta de la marca de agua dependiendo del entorno."""
    base_path = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
    return os.path.join(base_path, "../img/watermark.png")

def load_watermark():
    """Carga la marca de agua en memoria aplicándole transparencia."""
    watermark = Image.open(get_watermark_path()).convert("RGBA")
    new_data = [
        (r, g, b, 200) if (r, g, b) == (255, 255, 255) else (r, g, b, a)
        for r, g, b, a in watermark.getdata()
    ]
    watermark.putdata(new_data)
    return watermark
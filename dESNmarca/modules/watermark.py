import os
import sys
from PIL import Image, ImageEnhance  # type: ignore
from tkinter import filedialog, messagebox

OPACITY = 0.9  # Transparecia al 80%

def get_watermark_path():
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(__file__)
    return os.path.join(base_path, "img", "watermark.png")

def set_opacity(img, opacity):
    """
    Aplica opacidad a una imagen preservando su canal alfa original.
    opacity debe estar entre 0 (transparente) y 1 (opaco).
    """
    if img.mode != "RGBA":
        img = img.convert("RGBA")

    alpha = img.getchannel("A")
    alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
    img.putalpha(alpha)
    return img

def load_watermark():
    watermark_path = get_watermark_path()
    if not os.path.exists(watermark_path):
        raise FileNotFoundError(f"Watermark not found at: {watermark_path}")
    
    watermark_image = Image.open(watermark_path).convert("RGBA")
    watermark_image = set_opacity(watermark_image, OPACITY)
    return watermark_image

def select_custom_watermark(watermark_container):
    """Permite seleccionar una imagen para usarla como watermark personalizada."""
    custom_watermark_file = filedialog.askopenfilename(
        filetypes=[("Archivos de Imagen", "*.png *.jpg *.jpeg *.bmp *.tiff")]
    )
    if not custom_watermark_file:
        return

    try:
        watermark_image = Image.open(custom_watermark_file).convert("RGBA")
        watermark_con_transparencia = set_opacity(watermark_image, OPACITY)
        watermark_container[0] = watermark_con_transparencia  # Actualiza la watermark
        messagebox.showinfo("Marca de Agua Actualizada",
                            "La marca de agua personalizada se ha cargado correctamente.")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo cargar la marca de agua: {e}")
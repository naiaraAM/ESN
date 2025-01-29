import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image
import sys

def resource_path(relative_path):
    """ Obtiene la ruta absoluta al recurso, funciona para PyInstaller """
    try:
        # PyInstaller usa una carpeta temporal y almacena el path en _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def select_folder():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        process_images(folder_selected)

def process_images(folder):
    # Obtener el directorio padre para guardar las imágenes procesadas
    parent_dir = os.path.dirname(folder)
    output_folder = os.path.join(parent_dir, folder, f"marca_de_agua")
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    # Cargar la marca de agua desde el recurso
    watermark_path = resource_path("marca_de_agua.png")
    if not os.path.exists(watermark_path):
        messagebox.showwarning("Advertencia", f"No se encontró la imagen de la marca de agua en {watermark_path}.")
        return

    # Obtener la ruta absoluta de la marca de agua para excluirla del procesamiento


    watermark = Image.open(watermark_path).convert("RGBA")
    # Convertir el fondo blanco de la marca de agua en transparente
    datas = watermark.getdata()

    newData = []
    for item in datas:
        pixels = item[:3]  # Obtener los primeros 3 valores (RGB)
        # if pixel is white, make it transparent 80%
        if all([pixel == 255 for pixel in pixels]):
            newData.append((255, 255, 255, 204))
        else:
            newData.append(item)

    watermark.putdata(newData)

    # Determinar el método de resampling adecuado
    try:
        resample_method = Image.LANCZOS  # Para Pillow >= 9.1.0
    except AttributeError:
        resample_method = Image.ANTIALIAS  # Para versiones anteriores

    # Procesar cada archivo en la carpeta
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)

        # Obtener la ruta absoluta del archivo
        file_abs_path = os.path.abspath(file_path)

        # Saltar la imagen de la marca de agua si está en la misma carpeta
        if file_abs_path == watermark_path:
            continue  # Saltar esta iteración

        try:
            with Image.open(file_path) as image:
                image = image.convert("RGBA")

                # Redimensionar la marca de agua proporcionalmente al tamaño de la imagen
                scale_ratio = min(image.size[0], image.size[1]) * 0.25 / max(watermark.size)
                new_size = (int(watermark.size[0]*scale_ratio), int(watermark.size[1]*scale_ratio))
                watermark_resized = watermark.resize(new_size, resample=resample_method)

                # Posicionar la marca de agua en la esquina inferior derecha
                position_from_bottom_percent = 0.05
                position_from_right_percent = 0.00
                position = (int(image.size[0] * (1 - position_from_right_percent) - watermark_resized.size[0]),
                            int(image.size[1] * (1 - position_from_bottom_percent) - watermark_resized.size[1]))

                # Combinar la imagen original con la marca de agua
                image.paste(watermark_resized, position, watermark_resized)

                # Guardar la imagen con el nuevo nombre
                base_name, ext = os.path.splitext(filename)
                new_filename = f"{base_name}_marca{ext}"
                output_path = os.path.join(output_folder, new_filename)
                image.convert("RGB").save(output_path, quality=95)
        except Exception as e:
            # Si no se puede abrir el archivo como imagen, lo saltamos
            print(f"No se pudo procesar el archivo {filename}: {e}")
            continue

    messagebox.showinfo("Proceso completado", f"Las imágenes se han guardado en {output_folder}")

# Crear la interfaz gráfica
window = tk.Tk()
window.title("Aplicador de Marca de Agua")

label = tk.Label(window, text="Entra en la carpeta de fotos:")
label.pack(pady=10)

button_select = tk.Button(window, text="Seleccionar Carpeta", command=select_folder)
button_select.pack(pady=5)

window.mainloop()
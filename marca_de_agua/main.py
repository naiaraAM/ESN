import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image # type: ignore
from converter import to_jpg
import piexif # type: ignore
from concurrent.futures import ThreadPoolExecutor


def get_watermark_path():
    """ Obtiene la ruta de la marca de agua dependiendo del entorno """
    base_path = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
    return os.path.join(base_path, "marca_de_agua.png")


def load_watermark():
    """ Carga la marca de agua en memoria con transparencia aplicada """
    watermark = Image.open(get_watermark_path()).convert("RGBA")
    new_data = [(r, g, b, 204) if (r, g, b) == (255, 255, 255) else (r, g, b, a) for r, g, b, a in watermark.getdata()]
    watermark.putdata(new_data)
    return watermark


# Cargar la marca de agua una sola vez
WATERMARK = load_watermark()


def clean_filename(filename):
    return "".join(c for c in filename if c.isalnum() or c in "._- ")


def apply_orientation(image):
    """ Aplica la orientación correcta basándose en los datos EXIF """
    try:
        exif_dict = piexif.load(image.info['exif'])
        orientation = exif_dict['0th'].get(274, 1)
        transformations = {
            2: lambda img: img.transpose(Image.FLIP_LEFT_RIGHT),
            3: lambda img: img.transpose(Image.ROTATE_180),
            4: lambda img: img.transpose(Image.FLIP_TOP_BOTTOM),
            5: lambda img: img.transpose(Image.FLIP_LEFT_RIGHT).transpose(Image.ROTATE_90),
            6: lambda img: img.transpose(Image.ROTATE_270),
            7: lambda img: img.transpose(Image.FLIP_LEFT_RIGHT).transpose(Image.ROTATE_270),
            8: lambda img: img.transpose(Image.ROTATE_90),
        }
        return transformations.get(orientation, lambda img: img)(image)
    except (KeyError, AttributeError, ValueError):
        return image


def process_image(file_path, output_folder):
    """ Procesa una imagen agregando la marca de agua y guardándola en la carpeta de salida """
    try:
        with Image.open(file_path) as image:
            exif_data = image.info.get('exif')
            image = apply_orientation(image).convert("RGBA")

            # Redimensionar la marca de agua al 25% del tamaño más pequeño de la imagen
            scale_ratio = min(image.size) * 0.25 / max(WATERMARK.size)
            watermark_resized = WATERMARK.resize((int(WATERMARK.width * scale_ratio), int(WATERMARK.height * scale_ratio)), Image.LANCZOS)

            # Posicionar la marca de agua en la esquina inferior derecha
            position = (
                image.width - watermark_resized.width,
                image.height - watermark_resized.height - int(image.height * 0.05)
            )

            # Componer la imagen final
            final_image = image.copy()
            final_image.alpha_composite(watermark_resized, position)
            final_image = final_image.convert("RGB")  # Convertir a RGB para guardar

            # Guardar la imagen con EXIF si está presente
            output_path = os.path.join(output_folder, clean_filename(os.path.basename(file_path)))
            if exif_data:
                exif_dict = piexif.load(exif_data)
                exif_dict["0th"][274] = 1  # Corregir la orientación
                final_image.save(output_path, quality=100, exif=piexif.dump(exif_dict))
            else:
                final_image.save(output_path, quality=100)
    except Exception as e:
        print(f"Error procesando {file_path}: {e}")


def process_images(folder_selected, progress_window, progress_label, progress_var):
    """ Procesa todas las imágenes en paralelo """
    to_jpg(folder_selected)
    jpg_folder = os.path.join(folder_selected, "jpg")
    files = [os.path.join(jpg_folder, f) for f in os.listdir(jpg_folder) if f.lower().endswith(('png', 'jpg', 'jpeg', 'tiff', 'bmp'))]
    
    if not files:
        messagebox.showerror("Error", "No se encontraron imágenes en la carpeta seleccionada.")
        return

    output_folder = os.path.join(folder_selected, "marca_de_agua")
    os.makedirs(output_folder, exist_ok=True)

    total_files = len(files)

    def update_progress(i):
        """ Actualiza la barra de progreso en la GUI """
        progress_var.set((i + 1) / total_files * 100)
        progress_label.config(text=f"Procesando {i + 1}/{total_files} imágenes")
        progress_window.after(100)

    def worker(i, file):
        """ Función ejecutada por cada hilo para procesar imágenes """
        process_image(file, output_folder)
        update_progress(i)

    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(worker, i, file): i for i, file in enumerate(files)}
        for future in futures:
            future.result()  # Esperar a que todas las imágenes terminen de procesarse
    
    progress_window.quit()
    # eliminala carpeta jpg incluso si no está vacía
    for file in files:
        os.remove(file)
    os.rmdir(jpg_folder)


def select_folder():
    folder_selected = filedialog.askdirectory()
    if not folder_selected:
        return
    
    progress_window = tk.Toplevel()
    progress_window.title("Procesando Imágenes")
    progress_window.geometry("400x150")

    ttk.Label(progress_window, text="Procesando imágenes...").pack(pady=10)

    progress_var = tk.DoubleVar()
    ttk.Progressbar(progress_window, variable=progress_var, maximum=100).pack(pady=10, padx=20, fill=tk.X)

    progress_label = ttk.Label(progress_window, text="Iniciando...")
    progress_label.pack()

    thread = threading.Thread(target=process_images, args=(folder_selected, progress_window, progress_label, progress_var))
    thread.daemon = True
    thread.start()

    progress_window.mainloop()
    progress_window.destroy()
    messagebox.showinfo("Proceso Completado", "Las imágenes se han guardado en la carpeta 'marca_de_agua'")


def create_main_window():
    """ Crea la ventana principal de la aplicación """
    root = tk.Tk()
    root.title("Marca de Agua")
    root.geometry("350x250")
    root.resizable(False, False)

    ttk.Label(root, text="Añadir Marca de Agua a Imágenes", font=("Arial", 14)).pack(pady=10)
    ttk.Button(root, text="Seleccionar Carpeta", command=select_folder).pack(pady=20)

    ttk.Label(root, text="Listo", relief=tk.SUNKEN, anchor=tk.W).pack(side=tk.BOTTOM, fill=tk.X)

    root.mainloop()

# Ejecutar la aplicación
if __name__ == "__main__":
    create_main_window()
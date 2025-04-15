import os
import piexif  # type: ignore
import shutil

from PIL import Image  # type: ignore
from tkinter import messagebox
from concurrent.futures import ThreadPoolExecutor


def clean_filename(filename):
    return "".join(c for c in filename if c.isalnum() or c in "._- ")

def apply_orientation(image):
    """Aplica la orientación correcta basándose en los datos EXIF."""
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

def process_image(file_path, output_folder, watermark_pos, watermark):
    """Procesa una imagen agregándole la marca de agua en una posición específica."""
    try:
        with Image.open(file_path) as image:
            exif_data = image.info.get('exif')
            image = apply_orientation(image).convert("RGBA")
            # Redimensionar la marca de agua al 25% del tamaño mínimo de la imagen
            scale_ratio = min(image.size) * 0.25 / max(watermark.size)
            watermark_resized = watermark.resize(
                (int(watermark.width * scale_ratio), int(watermark.height * scale_ratio)),
                Image.LANCZOS
            )
            # Calcular la posición según el parámetro
            if watermark_pos == "top_left":
                position = (0, int(image.height * 0.05))
            elif watermark_pos == "top_center":
                position = ((image.width - watermark_resized.width) // 2, 0)
            elif watermark_pos == "top_right":
                position = (image.width - watermark_resized.width, int(image.height * 0.05))
            elif watermark_pos == "bottom_left":
                position = (0, image.height - watermark_resized.height - int(image.height * 0.05))
            elif watermark_pos == "bottom_center":
                position = ((image.width - watermark_resized.width) // 2,
                            image.height - watermark_resized.height)
            elif watermark_pos == "bottom_right":
                position = (image.width - watermark_resized.width,
                            image.height - watermark_resized.height - int(image.height * 0.05))
            else:
                # Valor por defecto: esquina inferior derecha
                position = (image.width - watermark_resized.width,
                            image.height - watermark_resized.height)
                            
            final_image = image.copy()
            final_image.alpha_composite(watermark_resized, position)
            final_image = final_image.convert("RGB")  # Convertir a RGB para guardar
            
            # Guardar la imagen con EXIF si está presente
            output_path = os.path.join(output_folder, clean_filename(os.path.basename(file_path)))
            if exif_data:
                exif_dict = piexif.load(exif_data)
                exif_dict["0th"][274] = 1  # Corregir orientación
                final_image.save(output_path, quality=100, exif=piexif.dump(exif_dict))
            else:
                final_image.save(output_path, quality=100)
    except Exception as e:
        print(f"Error procesando {file_path}: {e}")

def process(folder_selected, progress_window, progress_label, progress_var, watermark_pos, to_jpg, watermark, type="directory"):
    
    if type == "file":
        # folder_selected es la ruta del archivo
        to_jpg(folder_selected, type)
        # Usar el directorio del archivo para construir la carpeta jpg
        jpg_folder = os.path.join(os.path.dirname(folder_selected), "jpg")
        # Se asume que el archivo convertido se conserva el mismo nombre
        file_converted = os.path.join(jpg_folder, os.path.basename(folder_selected))
        files = [file_converted]
        # La carpeta de salida estará en el mismo directorio que el archivo original
        output_folder = os.path.join(os.path.dirname(folder_selected), "watermark")
    else:
        # Caso directorio
        to_jpg(folder_selected, type)
        jpg_folder = os.path.join(folder_selected, "jpg")
        files = [os.path.join(jpg_folder, f) for f in os.listdir(jpg_folder)
                 if f.lower().endswith(('png', 'jpg', 'jpeg', 'tiff', 'bmp'))]
        # La carpeta de salida debe estar en el directorio seleccionado, no dentro de la carpeta jpg
        output_folder = os.path.join(folder_selected, "watermark")
    
    if not files:
        messagebox.showerror("Error", "No se encontraron imágenes en la carpeta seleccionada.")
        return

    os.makedirs(output_folder, exist_ok=True)
    total_files = len(files)

    def update_progress(i):
        progress_var.set((i + 1) / total_files * 100)
        progress_label.configure(text=f"Procesando {i + 1}/{total_files} imágenes")
        progress_window.after(100)

    def worker(i, file):
        from modules.processing import process_image
        process_image(file, output_folder, watermark_pos, watermark)
        update_progress(i)

    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(worker, i, file): i for i, file in enumerate(files)}
        for future in futures:
            future.result()

    progress_window.quit()
    # Eliminar carpeta jpg
    for file in files:
        try:
            os.remove(file)
        except Exception as e:
            print(f"Error al eliminar {file}: {e}")
    try:
        shutil.rmtree(jpg_folder)
    except Exception as e:
        print(f"Error al eliminar la carpeta {jpg_folder}: {e}")
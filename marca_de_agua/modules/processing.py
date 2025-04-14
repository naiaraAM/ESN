import os
from PIL import Image  # type: ignore
import piexif  # type: ignore

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

def process_images(folder_selected, progress_window, progress_label, progress_var, watermark_pos, to_jpg, watermark):
    """Procesa todas las imágenes en paralelo usando la posición de watermark especificada."""
    # Convertir imágenes a JPG (se asume que la función to_jpg ya está definida)
    to_jpg(folder_selected)
    jpg_folder = os.path.join(folder_selected, "jpg")
    files = [os.path.join(jpg_folder, f) for f in os.listdir(jpg_folder)
             if f.lower().endswith(('png', 'jpg', 'jpeg', 'tiff', 'bmp'))]
    
    if not files:
        from tkinter import messagebox
        messagebox.showerror("Error", "No se encontraron imágenes en la carpeta seleccionada.")
        return

    output_folder = os.path.join(folder_selected, "watermark")
    os.makedirs(output_folder, exist_ok=True)
    total_files = len(files)

    def update_progress(i):
        progress_var.set((i + 1) / total_files * 100)
        progress_label.configure(text=f"Procesando {i + 1}/{total_files} imágenes")
        progress_window.after(100)

    def worker(i, file):
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
        os.remove(file)
    os.rmdir(jpg_folder)
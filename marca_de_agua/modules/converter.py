import os
from PIL import Image # type: ignore
import piexif # type: ignore
from concurrent.futures import ThreadPoolExecutor
import pillow_heif # type: ignore

pillow_heif.register_heif_opener()

def process_image(file_path, jpg_folder):
    try:
        with Image.open(file_path) as image:
            exif_bytes = None
            if "exif" in image.info and image.info["exif"]:
                try:
                    exif_dict = piexif.load(image.info["exif"])
                    orientation = exif_dict["0th"].get(piexif.ImageIFD.Orientation, 1)
                    if orientation == 3:
                        image = image.rotate(180, expand=True)
                    elif orientation == 6:
                        image = image.rotate(270, expand=True)
                    elif orientation == 8:
                        image = image.rotate(90, expand=True)
                    # Eliminar orientación para evitar reorientación al abrir
                    exif_dict["0th"].pop(piexif.ImageIFD.Orientation, None)
                    exif_bytes = piexif.dump(exif_dict)
                except:
                    pass

            output_path = (
                os.path.splitext(os.path.join(jpg_folder, os.path.basename(file_path)))[0]
                + ".jpg"
            )
            if exif_bytes:
                image.convert("RGB").save(output_path, quality=100, exif=exif_bytes)
            else:
                image.convert("RGB").save(output_path, quality=100)
    except Exception as e:
        print(f"Error processing {file_path}: {e}")

def to_jpg(input_path, type="directory"):
    if type == "file":
        # a single file
        jpg_folder = os.path.join(os.path.dirname(input_path), "jpg")
        os.makedirs(jpg_folder, exist_ok=True)
        process_image(input_path, jpg_folder)
    elif type == "directory":
        jpg_folder = os.path.join(input_path, "jpg")
        os.makedirs(jpg_folder, exist_ok=True)  # Crear la carpeta 'jpg' si no existe

        files = [os.path.join(input_path, filename) for filename in os.listdir(input_path)
                if os.path.isfile(os.path.join(input_path, filename)) and filename.lower().endswith(('png', 'jpg', 'jpeg', 'tiff', 'bmp', 'heic'))]

        with ThreadPoolExecutor() as executor:
            executor.map(lambda file_path: process_image(file_path, jpg_folder), files)
import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image  # type: ignore
from modules.processing import process_images
from modules.converter import to_jpg  # Se asume que esta función ya existe en el proyecto
from modules.watermark import load_watermark

def select_folder(root, main_frame, watermark_container):
    folder_selected = filedialog.askdirectory()
    if not folder_selected:
        return

    # Limpiar el contenido del marco principal
    for widget in main_frame.winfo_children():
        widget.destroy()

    btn_frame = ttk.Frame(main_frame, padding=20)
    title_label = ttk.Label(main_frame, text="Selecciona la posición", style="Title.TLabel")
    title_label.pack(pady=(0, 25))
    btn_frame.pack(expand=True, fill=tk.BOTH)

    def on_select_position(position):
        progress_window = tk.Toplevel(root)
        progress_window.title("Procesando imágenes")
        progress_window.geometry("400x150")
        ttk.Label(progress_window, text="Procesando imágenes...").pack(pady=10)
        progress_var = tk.DoubleVar()
        ttk.Progressbar(progress_window, variable=progress_var, maximum=100).pack(pady=10, padx=20, fill=tk.X)
        progress_label = ttk.Label(progress_window, text="Iniciando...")
        progress_label.pack()
        # Pasar la marca de agua actual (puede ser actualizada desde la opción personalizada)
        thread = threading.Thread(target=process_images, args=(
            folder_selected, progress_window, progress_label, progress_var, position, to_jpg, watermark_container[0]))
        thread.daemon = True
        thread.start()
        progress_window.mainloop()
        progress_window.destroy()
        messagebox.showinfo("Proceso Completado",
                            "Las imágenes se han guardado en la carpeta 'watermark' dentro de la carpeta seleccionada.")
        output_folder = os.path.join(folder_selected, "watermark")
        os.startfile(output_folder)
        # Volver a la pantalla de inicio: limpiar y recrear el contenido inicial
        for widget in main_frame.winfo_children():
            widget.destroy()
        title_label = ttk.Label(main_frame, text="Añadir watermark a Imágenes", style="Title.TLabel")
        title_label.pack(pady=(0, 25))
        select_button = ttk.Button(main_frame, text="Seleccionar Carpeta",
                                   command=lambda: select_folder(root, main_frame, watermark_container))
        select_button.pack(ipadx=10, pady=5)
        watermark_button = ttk.Button(main_frame, text="Seleccionar watermark personalizada",
                                      command=lambda: select_custom_watermark(root, watermark_container))
        watermark_button.pack(ipadx=10, pady=5)

    # Definir las opciones de posición
    options = [
        ("↖", "top_left", (0, 0)),
        ("↑", "top_center", (0, 1)),
        ("↗", "top_right", (0, 2)),
        ("↙", "bottom_left", (1, 0)),
        ("↓", "bottom_center", (1, 1)),
        ("↘", "bottom_right", (1, 2)),
    ]

    # Configura las columnas para que se distribuyan equitativamente
    for col in range(3):
        btn_frame.columnconfigure(col, weight=1)

    for text, pos, coords in options:
        row, col = coords
        button = ttk.Button(btn_frame, text=text, command=lambda cmd=pos: on_select_position(cmd))
        button.grid(row=row, column=col, padx=10, pady=30, sticky="ew")

    for child in btn_frame.winfo_children():
        child.grid_configure(padx=5, pady=20)

def select_custom_watermark(root, watermark_container):
    custom_watermark_file = filedialog.askopenfilename(
        filetypes=[("Archivos de Imagen", "*.png;*.jpg;*.jpeg;*.bmp;*.tiff")])
    if custom_watermark_file:
        try:
            watermark_image = Image.open(custom_watermark_file).convert("RGBA")
            new_data = [
                (r, g, b, 200) if (r, g, b) == (255, 255, 255) else (r, g, b, a)
                for r, g, b, a in watermark_image.getdata()
            ]
            watermark_image.putdata(new_data)
            # Actualizar la marca de agua en el contenedor mutable
            watermark_container[0] = watermark_image
            messagebox.showinfo("Marca de Agua Actualizada",
                                "La marca de agua personalizada se ha cargado correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar la marca de agua: {e}")

def create_main_window():
    """Crea la ventana principal de la aplicación con estilo moderno."""
    root = tk.Tk()
    root.title("Marca de Agua")
    root.geometry("420x300")
    icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../img/icon.ico"))
    if os.path.exists(icon_path):
        root.iconbitmap(icon_path)
    root.configure(bg="white")
    root.resizable(False, False)

    # Estilo personalizado
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TLabel", font=("Kelson Sans", 12))
    style.configure("Title.TLabel", font=("Lato", 16, "bold"))
    style.configure("TButton", font=("Lato", 11), padding=6)
    
    # Frame principal
    main_frame = ttk.Frame(root, padding=30)
    main_frame.pack(expand=True)

    # Título
    title_label = ttk.Label(main_frame, text="Añadir watermark", style="Title.TLabel")
    title_label.pack(pady=(0, 25))

    # Usar un contenedor mutable (lista) para poder actualizar la marca de agua
    watermark_container = [load_watermark()]

    # Botón para seleccionar carpeta
    select_button = ttk.Button(main_frame, text="Seleccionar Carpeta",
                               command=lambda: select_folder(root, main_frame, watermark_container))
    select_button.pack(ipadx=10, pady=5)

    # Botón para seleccionar una marca de agua personalizada
    watermark_button = ttk.Button(main_frame, text="Seleccionar watermark personalizada",
                                  command=lambda: select_custom_watermark(root, watermark_container))
    watermark_button.pack(ipadx=10, pady=5)

    root.mainloop()
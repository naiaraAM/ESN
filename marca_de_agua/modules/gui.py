#!/usr/bin/env python3
import os
import threading
import customtkinter as ctk  # type: ignore
from tkinter import filedialog, messagebox
from PIL import Image  # type: ignore

from modules.processing import process
from modules.converter import to_jpg  # Se asume que esta función ya existe en el proyecto
from modules.watermark import load_watermark

# Paleta de colores
colors = {
    'pink': '#EC008C',
    'cyan': '#00AEEF',
    'green': '#7AC143',
    'orange': '#F47B20',
    'dark_blue': '#2E3192'
}

def select_folder(root, main_frame, watermark_container):
    """Permite seleccionar la carpeta a procesar y luego la posición del watermark."""
    folder_selected = filedialog.askdirectory()
    if not folder_selected:
        return

    # Se limpia el contenido del marco principal
    for widget in main_frame.winfo_children():
        widget.destroy()

    # Se crea un marco para los botones de posición
    btn_frame = ctk.CTkFrame(main_frame, 
                             corner_radius=5,
                             fg_color="white")
    btn_frame.pack(expand=True, padx=20, pady=20, fill="both")

    # Se agrega un título en la pantalla de selección de posición
    title_label = ctk.CTkLabel(main_frame, text="Selecciona la posición", font=("Lato", 16, "bold"))
    title_label.pack(pady=(0, 25))

    def on_select_position(position):
        """Inicia el procesamiento de imágenes según la posición elegida."""
        progress_window = ctk.CTkToplevel(root)
        progress_window.title("Procesando imágenes")
        progress_window.resizable(False, False)

        progress_window.geometry("400x150")

        progress_label = ctk.CTkLabel(progress_window, text="Procesando imágenes...", font=("Lato", 12))
        progress_label.pack(pady=10)

        progress_bar = ctk.CTkProgressBar(progress_window)
        progress_bar.set(0)
        progress_bar.pack(pady=10, padx=20, fill="x")
        # Se lanza el procesamiento en un hilo
        thread = threading.Thread(
            target=process,
            args=(folder_selected, 
                  progress_window, 
                  progress_label,
                  progress_bar, 
                  position, 
                  to_jpg, 
                  watermark_container[0], 
                  "directory")
        )
        thread.daemon = True
        thread.start()

        progress_window.mainloop()
        progress_window.destroy()

        messagebox.showinfo("Proceso Completado",
                            "Las imágenes se han guardado en la carpeta 'watermark' dentro de la carpeta seleccionada.")
        output_folder = os.path.join(folder_selected, "watermark")
        os.makedirs(output_folder, exist_ok=True)  # Asegura que la carpeta existe
        os.startfile(output_folder)

        # Volver a la pantalla de inicio
        init_main_screen(root, main_frame, watermark_container)

    # Opciones de posición con sus respectivos iconos y coordenadas en el grid
    options = [
        ("↖", "top_left", (0, 0)),
        ("↑", "top_center", (0, 1)),
        ("↗", "top_right", (0, 2)),
        ("↙", "bottom_left", (1, 0)),
        ("↓", "bottom_center", (1, 1)),
        ("↘", "bottom_right", (1, 2)),
    ]

    # Creación de botones para seleccionar la posición
    for text, pos, coords in options:
        row, col = coords
        button = ctk.CTkButton(btn_frame,
                               text=text,
                               corner_radius=5,
                               fg_color=colors['cyan'],
                               text_color="white",
                               hover_color=colors['dark_blue'],
                                font=("Lato", 11),
                               command=lambda p=pos: on_select_position(p))
        button.grid(row=row, column=col, padx=10, pady=30, sticky="ew")

    # Configurar la distribución de columnas del grid
    for col in range(3):
        btn_frame.grid_columnconfigure(col, weight=1)

def select_single_image(root, main_frame, watermark_container):
    """Permite seleccionar una imagen única, elegir la posición y aplicarle el watermark."""
    # Seleccionar imagen única
    image_file = filedialog.askopenfilename(
        filetypes=[("Archivos de Imagen", "*.png;*.jpg;*.jpeg;*.bmp;*.tiff")]
    )
    if not image_file:
        return
    
    folder_selected = os.path.dirname(image_file)
    if not folder_selected:
        return

    # Se limpia el contenido del marco principal
    for widget in main_frame.winfo_children():
        widget.destroy()

    # Se crea un marco para los botones de posición
    btn_frame = ctk.CTkFrame(main_frame, 
                             corner_radius=5,
                             fg_color="white")
    btn_frame.pack(expand=True, padx=20, pady=20, fill="both")

    # Se agrega un título en la pantalla de selección de posición
    title_label = ctk.CTkLabel(main_frame, text="Selecciona la posición", font=("Lato", 16, "bold"))
    title_label.pack(pady=(0, 25))

    def on_select_position(position):
        """Inicia el procesamiento de imágenes según la posición elegida."""
        progress_window = ctk.CTkToplevel(root)
        progress_window.title("Procesando imágenes")
        progress_window.geometry("400x150")

        progress_label = ctk.CTkLabel(progress_window, text="Procesando imágenes...", font=("Lato", 12))
        progress_label.pack(pady=10)

        progress_bar = ctk.CTkProgressBar(progress_window)
        progress_bar.set(0)
        progress_bar.pack(pady=10, padx=20, fill="x")
        
        # Se lanza el procesamiento en un hilo
        thread = threading.Thread(
            target=process,
            args=(image_file, 
                  progress_window, 
                  progress_label, 
                  progress_bar, 
                  position, 
                  to_jpg, 
                  watermark_container[0], 
                  "file")
        )
        thread.daemon = True
        thread.start()

        progress_window.mainloop()
        progress_window.destroy()

        messagebox.showinfo("Proceso Completado",
                            "Las imágenes se han guardado en la carpeta 'watermark' dentro de la carpeta seleccionada.")
        output_folder = os.path.join(folder_selected, "watermark")
        os.makedirs(output_folder, exist_ok=True)  # Asegura que la carpeta existe
        os.startfile(output_folder)

        # Volver a la pantalla de inicio
        init_main_screen(root, main_frame, watermark_container)

    # Opciones de posición con sus respectivos iconos y coordenadas en el grid
    options = [
        ("↖", "top_left", (0, 0)),
        ("↑", "top_center", (0, 1)),
        ("↗", "top_right", (0, 2)),
        ("↙", "bottom_left", (1, 0)),
        ("↓", "bottom_center", (1, 1)),
        ("↘", "bottom_right", (1, 2)),
    ]

    # TODO: Añadir label que ponga posicion

    # Creación de botones para seleccionar la posición
    for text, pos, coords in options:
        row, col = coords
        button = ctk.CTkButton(btn_frame,
                               text=text,
                               corner_radius=5,
                               fg_color=colors['cyan'],
                               text_color="white",
                               hover_color=colors['dark_blue'],
                                font=("Lato", 11),
                               command=lambda p=pos: on_select_position(p))
        button.grid(row=row, column=col, padx=10, pady=30, sticky="ew")

    # Configurar la distribución de columnas del grid
    for col in range(3):
        btn_frame.grid_columnconfigure(col, weight=1)

def init_main_screen(root, main_frame, watermark_container):
    """Inicializa la pantalla principal de la aplicación."""
    for widget in main_frame.winfo_children():
        widget.destroy()

    title_label = ctk.CTkLabel(main_frame,
                               text="Añadir watermark",
                               font=("Kelson Sans", 16, "bold"),
                               text_color=colors['dark_blue'])
    title_label.pack(pady=(0, 25))

    select_folder = ctk.CTkButton(main_frame,
                                  text="Seleccionar Carpeta",
                                  corner_radius=5,
                                  fg_color=colors['cyan'],
                                  text_color="white",
                                  hover_color=colors['dark_blue'],
                                  font=("Lato", 12),
                                  command=lambda: select_folder(root, main_frame, watermark_container))
    select_folder.pack(ipadx=10, pady=5)

    single_image_button = ctk.CTkButton(main_frame,
                                    text="Seleccionar imgen única",
                                    corner_radius=5,
                                    fg_color=colors['cyan'],
                                    text_color="white",
                                    hover_color=colors['dark_blue'],
                                    font=("Lato", 12),
                                    command=lambda: select_single_image(root, main_frame, watermark_container))

    single_image_button.pack(ipadx=10, pady=5)

    watermark_button = ctk.CTkButton(main_frame,
                                     text="Seleccionar watermark personalizada",
                                     corner_radius=5,
                                     fg_color=colors['cyan'],
                                     text_color="white",
                                     hover_color=colors['dark_blue'],
                                     font=("Lato", 12),
                                     command=lambda: select_custom_watermark(root, watermark_container))
    watermark_button.pack(ipadx=10, pady=5)

    footer_label = ctk.CTkLabel(main_frame,
                                text="© ESN Santander",
                                font=("Lato", 12),
                                text_color=colors['dark_blue'])
    footer_label.pack(side="bottom", pady=(20, 0))

def select_custom_watermark(root, watermark_container):
    """Permite seleccionar una imagen para usarla como watermark personalizada."""
    custom_watermark_file = filedialog.askopenfilename(
        filetypes=[("Archivos de Imagen", "*.png *.jpg *.jpeg *.bmp *.tiff")]
    )
    if not custom_watermark_file:
        return

    try:
        watermark_image = Image.open(custom_watermark_file).convert("RGBA")
        new_data = [
            (r, g, b, 200) if (r, g, b) == (255, 255, 255) else (r, g, b, a)
            for r, g, b, a in watermark_image.getdata()
        ]
        watermark_image.putdata(new_data)
        watermark_container[0] = watermark_image  # Se actualiza la marca de agua
        messagebox.showinfo("Marca de Agua Actualizada",
                            "La marca de agua personalizada se ha cargado correctamente.")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo cargar la marca de agua: {e}")

def create_main_window():
    """Crea y configura la ventana principal utilizando CustomTkinter."""
    ctk.set_appearance_mode("Light")  # o "Dark"
    ctk.set_default_color_theme("blue")  # Se puede definir otra paleta si se desea

    root = ctk.CTk()
    root.title("Marca de Agua")
    root.geometry("420x300")
    icon_path = os.path.join(os.path.dirname(__file__), "../img/icon.ico")
    if os.path.exists(icon_path):
        root.iconbitmap(icon_path)
    root.resizable(False, False)

    # Se crea el marco principal con esquinas redondeadas
    main_frame = ctk.CTkFrame(root, 
                              corner_radius=5, 
                              fg_color="white"
                              )
    main_frame.pack(expand=True, fill="both", padx=30, pady=30)
    title_label = ctk.CTkLabel(main_frame, text="Añadir watermark",
                               font=("Lato", 16, "bold"),
                               text_color=colors['dark_blue'])
    title_label.pack(pady=(0, 25))

    # Contenedor mutable para la marca de agua (lista de un elemento)
    watermark_container = [load_watermark()]

    select_button = ctk.CTkButton(main_frame,
                                  text="Seleccionar Carpeta",
                                  corner_radius=5,
                                  fg_color=colors['cyan'],
                                  text_color="white",
                                  hover_color=colors['dark_blue'],
                                  font=("Lato", 11),
                                  command=lambda: select_folder(root, main_frame, watermark_container))
    select_button.pack(ipadx=10, pady=5)

    single_image_button = ctk.CTkButton(main_frame,
                                    text="Seleccionar imgen única",
                                    corner_radius=5,
                                    fg_color=colors['cyan'],
                                    text_color="white",
                                    hover_color=colors['dark_blue'],
                                    font=("Lato", 11),
                                    command=lambda: select_single_image(root, main_frame, watermark_container))

    single_image_button.pack(ipadx=10, pady=5)

    watermark_button = ctk.CTkButton(main_frame,
                                     text="Seleccionar watermark personalizada",
                                     corner_radius=5,
                                     fg_color=colors['cyan'],
                                     text_color="white",
                                     hover_color=colors['dark_blue'],
                                     font=("Lato", 11),
                                     command=lambda: select_custom_watermark(root, watermark_container))
    watermark_button.pack(ipadx=10, pady=5)

    # Footer
    footer_label = ctk.CTkLabel(main_frame,
                                text="© ESN Santander",
                                font=("Kelson Sans", 12),
                                text_color=colors['dark_blue'])
    footer_label.pack(side="bottom", pady=(20, 0))

    root.mainloop()
# gui_app.py

import tkinter
from tkinter import simpledialog
import customtkinter as ctk
from customtkinter import CTkFont
import threading
from typing import Optional, Dict, List, Any
import queue
import logging
import sys
import os
import json
import webbrowser
from PIL import Image

from network_interface_util import get_network_interfaces
from star_resonance_monitor_core import StarResonanceMonitor
from logging_config import setup_logging

# --- Log Queue Handler (unchanged) ---
class QueueHandler(logging.Handler):
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        self.log_queue.put(self.format(record))

# --- Standard Output Stream Redirection to Queue (unchanged) ---
class StreamToQueue:
    def __init__(self, text_queue):
        self.text_queue = text_queue

    def write(self, text):
        self.text_queue.put(text)

    def flush(self):
        pass

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("BPSR Module Optimizer by: MrSnake")
        self.iconbitmap("icon.ico")
        self.attributes("-topmost", True)
        self.geometry("1280x1080")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # --- Load Icon Font ---
        self.fa_font = self.load_font_awesome()

        self.monitor_thread: Optional[threading.Thread] = None
        self.monitor_instance: Optional[StarResonanceMonitor] = None
        self.interfaces = get_network_interfaces()
        self.interface_map = {f"{i}: {iface.get('description', iface['name'])}": iface['name'] 
                              for i, iface in enumerate(self.interfaces)}
        
        # --- Caching & Pagination ---
        self.all_solutions_cache: List[Any] = [] # Holds all raw solutions
        self.solutions_cache: List[Any] = [] # Holds filtered solutions for display
        self.distribution_filter = "All" # Current distribution filter
        self.current_page = 0
        self.results_per_page = 4 # Show 4 results per page
        
        # Main grid configuration for content and side console
        self.grid_columnconfigure(0, weight=1) # Column for main content
        self.grid_columnconfigure(1, weight=0) # Column for the console panel (initially no weight)
        self.grid_rowconfigure(0, weight=1) # Main row for all content

        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=0) # Column for social links

        # --- Language Selection ---
        self.translations = {
            "en": {
                "select_interface": "Select Network Interface:",
                "select_module_type": "Select Module Type:",
                "filter_attributes": "Filter Attributes (space separated):",
                "select_preset": "Select Preset Filter Attributes:",
                "recommended_combos": "Recommended combinations will only show the above filtered attributes, it is recommended to fill in all tolerable attributes.",
                "dynamic_instruction_1": "Before pressing the ",
                "dynamic_instruction_2": " button, move your character to a location with few players around.",
                "waiting_for_modules": "Waiting for modules to be combined",
                "change_channel_instruction": "Change channels in-game to start processing modules.",
                "refilter": "\uf002 Refilter",
                "save_preset_title": "Save Preset",
                "save_preset_prompt": "Enter a name for the current attribute selection:",
                "delete_preset_title": "Delete Preset",
                "delete_preset_prompt": "Are you sure you want to delete the preset '{preset_name}'?",
                "save": "💾 Save",
                "delete": "🗑️ Delete"
            },
            "es": {
                "select_interface": "Selecciona la Interfaz de Red:",
                "select_module_type": "Selecciona el Tipo de Módulo:",
                "filter_attributes": "Filtrar Atributos (separados por coma):",
                "select_preset": "Seleccionar Atributos de Filtro Predefinidos:",
                "recommended_combos": "Las combinaciones recomendadas solo mostrarán los atributos filtrados anteriormente, se recomienda rellenar todos los atributos tolerables.",
                "dynamic_instruction_1": "Antes de presionar el botón ",
                "dynamic_instruction_2": " mueve tu personaje a un lugar con pocos jugadores a tu alrededor.",
                "waiting_for_modules": "Espera a que combine los Modulos",
                "change_channel_instruction": "Cambia de canal dentro del juego para comenzar a procesar módulos.",
                "refilter": "\uf002 Refiltrar",
                "save_preset_title": "Guardar Preset",
                "save_preset_prompt": "Introduce un nombre para la selección de atributos actual:",
                "delete_preset_title": "Eliminar Preset",
                "delete_preset_prompt": "¿Estás seguro de que quieres eliminar el preset '{preset_name}'?",
                "save": "💾 Guardar",
                "delete": "🗑️ Eliminar"
            }
        }
        self.current_language = "en"

        # --- Title Frame ---
        title_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        title_frame.grid(row=0, column=0, pady=(10, 5), sticky="w", padx=10)

        app_icon_img = ctk.CTkImage(Image.open("icon.png"), size=(40, 40))
        app_icon = ctk.CTkLabel(title_frame, image=app_icon_img, text="")
        app_icon.pack(side="left", padx=(0, 10))

        self.title_label = ctk.CTkLabel(title_frame, text="BPSR Module Optimizer", font=("Segoe UI", 24, "bold"))
        self.title_label.pack(side="left")

        language_menu = ctk.CTkOptionMenu(title_frame, values=["English", "Español"], command=self.change_language)
        language_menu.pack(side="left", padx=20)
        language_menu.set("English")


        # --- Social Media Links ---
        social_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        social_frame.grid(row=0, column=1, pady=(10, 5), sticky="e")

        kick_img = ctk.CTkImage(Image.open("Icons/kick.png"), size=(24, 24))
        kick_icon = ctk.CTkLabel(social_frame, image=kick_img, text="", cursor="hand2")
        kick_icon.pack(side="left", padx=5)
        kick_icon.bind("<Button-1>", lambda e: webbrowser.open_new("https://kick.com/mrsnakevt"))

        youtube_img = ctk.CTkImage(Image.open("Icons/youtube.png"), size=(24, 24))
        youtube_icon = ctk.CTkLabel(social_frame, image=youtube_img, text="", cursor="hand2")
        youtube_icon.pack(side="left", padx=5)
        youtube_icon.bind("<Button-1>", lambda e: webbrowser.open_new("https://www.youtube.com/@MrSnake_VT"))

        x_img = ctk.CTkImage(Image.open("Icons/x-twitter.png"), size=(24, 24))
        x_icon = ctk.CTkLabel(social_frame, image=x_img, text="", cursor="hand2")
        x_icon.pack(side="left", padx=5)
        x_icon.bind("<Button-1>", lambda e: webbrowser.open_new("https://x.com/MrSnakeVT"))

        # --- Filter Frame (initially visible) ---
        self.filters_frame = ctk.CTkFrame(self.main_frame, fg_color="#495057")
        self.filters_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        self.filters_frame.grid_columnconfigure(0, weight=1)
        self.filters_frame.grid_columnconfigure(1, weight=1)
        self.filters_frame.grid_columnconfigure(2, weight=1)
        self.filters_frame.grid_columnconfigure(3, weight=1)

        # Column 0
        self.label_category = ctk.CTkLabel(self.filters_frame, text="Select Module Type:")
        self.label_category.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.category_menu = ctk.CTkOptionMenu(self.filters_frame, values=["All", "Attack", "Guard", "Support"])
        self.category_menu.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        self.category_menu.set("All")
        self.category_menu.configure(state="normal") # Ensure it's enabled initially

        self.label_interface = ctk.CTkLabel(self.filters_frame, text="Select Network Interface:")
        self.label_interface.grid(row=0, column=2, padx=10, pady=5, sticky="w")
        self.interface_menu = ctk.CTkOptionMenu(self.filters_frame, values=list(self.interface_map.keys()))
        self.interface_menu.grid(row=0, column=3, padx=10, pady=5, sticky="ew")

        # --- Presets Frame ---
        # --- Presets Frame ---
        self.presets_frame = ctk.CTkFrame(self.filters_frame, fg_color="#495057")
        self.presets_frame.grid(row=1, column=0, columnspan=4, padx=10, pady=(10,0), sticky="ew")
        self.presets_frame.grid_columnconfigure(0, weight=0)
        self.presets_frame.grid_columnconfigure(1, weight=1)
        self.presets_frame.grid_columnconfigure(2, weight=0)
        self.presets_frame.grid_columnconfigure(3, weight=0)

        self.label_presets = ctk.CTkLabel(self.presets_frame, text="Select Preset:")
        self.label_presets.grid(row=0, column=0, padx=(10, 5), pady=5, sticky="w")

        self.presets_menu = ctk.CTkOptionMenu(self.presets_frame, command=self.apply_preset)
        self.presets_menu.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.save_preset_button = ctk.CTkButton(self.presets_frame, text="", command=self.save_preset, width=80, corner_radius=8, fg_color="#2C2E33", border_color="#373a40", border_width=1)
        self.save_preset_button.grid(row=0, column=2, padx=5, pady=5)

        self.delete_preset_button = ctk.CTkButton(self.presets_frame, text="", command=self.delete_preset, width=80, corner_radius=8, fg_color="#2C2E33", border_color="#373a40", border_width=1)
        self.delete_preset_button.grid(row=0, column=3, padx=5, pady=5)

        self.attributes_buttons_frame = ctk.CTkFrame(self.filters_frame)
        self.attributes_buttons_frame.grid(row=2, column=0, columnspan=4, padx=10, pady=10, sticky="ew")

        self.all_attributes = [
            "DMG Stack", "Agile", "Life Condense", "First Aid", "Life Wave", "Life Steal", 
            "Team Luck & Crit", "Final Protection", "Strength Boost", "Agility Boost", 
            "Intellect Boost", "Special Attack", "Elite Strike", "Healing Boost", 
            "Healing Enhance", "Cast Focus", "Attack SPD", "Crit Focus", "Luck Focus", 
            "Resistance", "Armor"
        ]
        
        self.attribute_buttons: Dict[str, ctk.CTkButton] = {}
        self.selected_attributes = set()

        # --- Create "All" button ---
        all_button = ctk.CTkButton(
            self.attributes_buttons_frame,
            text="All",
            command=self.toggle_all_attributes,
            fg_color="#2C2E33",
            border_color="#373a40",
            border_width=1,
            corner_radius=8
        )
        all_button.grid(row=0, column=0, padx=5, pady=5)
        self.attribute_buttons["All"] = all_button

        # --- Create attribute buttons ---
        row, col = 0, 1
        for attr in self.all_attributes:
            if col > 6:  # Adjust number of columns as needed
                col = 0
                row += 1
            
            button = ctk.CTkButton(
                self.attributes_buttons_frame,
                text=attr,
                command=lambda a=attr: self.toggle_attribute(a),
                fg_color="#2C2E33",
                border_color="#373a40",
                border_width=1,
                corner_radius=8
            )
            button.grid(row=row, column=col, padx=5, pady=5)
            self.attribute_buttons[attr] = button
            col += 1

        self.control_frame = ctk.CTkFrame(self.main_frame)
        self.control_frame.grid(row=4, column=0, columnspan=2, pady=10)

        play_icon = ctk.CTkImage(Image.open("Icons/play.png"), size=(16, 16))
        self.start_button = ctk.CTkButton(self.control_frame, text="Start Monitoring", image=play_icon, command=self.start_monitoring)
        self.start_button.pack(side="left", padx=10)

        stop_icon = ctk.CTkImage(Image.open("Icons/stop.png"), size=(16, 16))
        self.stop_button = ctk.CTkButton(self.control_frame, text="Stop Monitoring", image=stop_icon, command=self.stop_monitoring, state="disabled")
        self.stop_button.pack(side="left", padx=10)
        
        self.rescreen_button = ctk.CTkButton(self.control_frame, text="", command=self.rescreen_results, state="disabled", font=self.fa_font)
        self.rescreen_button.pack(side="left", padx=10)

        # Button to toggle the console
        self.toggle_console_button = ctk.CTkButton(self.control_frame, text=">", command=self.toggle_console, width=30)
        self.toggle_console_button.pack(side="left", padx=10)

        # --- Dynamic Instructions ---
        self.instruction_frame = ctk.CTkFrame(self.main_frame, fg_color="#2B2B2B", corner_radius=10)
        self.instruction_frame.grid(row=5, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        
        self.instruction_icon = ctk.CTkLabel(self.instruction_frame, text="⚠️", font=("Segoe UI Emoji", 20), text_color="#FFCC00") # Yellow warning
        self.instruction_icon.pack(side="left", padx=(10, 5), pady=5)

        # Frame for complex, multi-part instruction
        self.instruction_text_frame = ctk.CTkFrame(self.instruction_frame, fg_color="transparent")
        self.instruction_text_frame.pack(side="left", padx=(0, 10), pady=5)

        self.update_dynamic_instruction()

        # Label for simple, single-part instructions
        self.instruction_label_simple = ctk.CTkLabel(self.instruction_frame, text="", font=("Segoe UI", 14))
        self.base_instruction_text = "" # For animation

        # --- Distribution Filter ---
        self.dist_filter_frame = ctk.CTkFrame(self.main_frame)
        self.dist_filter_frame.grid(row=6, column=0, columnspan=2, padx=10, pady=(5, 0), sticky="ew")
        self.dist_filter_frame.grid_remove() # Hide initially

        self.label_dist_filter = ctk.CTkLabel(self.dist_filter_frame, text="Attr. Distribution:")
        self.label_dist_filter.pack(side="left", padx=(10, 10))

        self.dist_filter_buttons: Dict[str, ctk.CTkButton] = {}
        filters = ["All", "Lv.5", "Lv.5/Lv.5", "Lv.5/Lv.6", "Lv.6/Lv.6"]
        for f in filters:
            btn = ctk.CTkButton(
                self.dist_filter_frame,
                text=f,
                command=lambda name=f: self.set_distribution_filter(name),
                width=70, # Ligeramente menos largo
                corner_radius=8 # Más redondeado
            )
            btn.pack(side="left", padx=5)
        self.dist_filter_buttons[f] = btn

        # --- Console Panel ---
        self.console_frame = ctk.CTkFrame(self, width=400)
        self.console_frame.grid(row=0, column=1, rowspan=2, padx=10, pady=10, sticky="ns")
        self.console_frame.grid_remove() # Hide by default

        self.console_frame.grid_rowconfigure(0, weight=1)
        self.console_frame.grid_columnconfigure(0, weight=1)

        log_font = ("Microsoft YaHei UI", 18, "bold")
        self.log_textbox = ctk.CTkTextbox(self.console_frame, state="disabled", wrap="word", font=log_font, spacing3=4)
        self.log_textbox.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        # --- Status Bar ---
        self.status_frame = ctk.CTkFrame(self)
        self.status_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="ew")
        self.status_label = ctk.CTkLabel(self.status_frame, text="Status: Idle", anchor="w")
        self.status_label.pack(side="left", padx=10, pady=2)

        self.log_queue = queue.Queue()
        logger_instance = logging.getLogger()
        logger_instance.setLevel(logging.INFO)
        logger_instance.addHandler(QueueHandler(self.log_queue))
        sys.stdout = StreamToQueue(self.log_queue)

        # --- New Progress Update Queue ---
        self.progress_queue = queue.Queue()
        self.results_queue = queue.Queue() # Queue for optimization results
        self.module_images = self.load_module_images() # Pre-load module images
        self.attribute_images = self.load_attribute_images() # Pre-load attribute icons

        # --- Results Display ---
        self.results_frame = ctk.CTkScrollableFrame(self.main_frame, label_text="Combinations")
        self.results_frame.grid(row=7, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        self.results_frame.grid_columnconfigure(0, weight=1)
        self.results_frame.grid_columnconfigure(1, weight=1)
        self.main_frame.grid_rowconfigure(7, weight=1) # Allow results frame to expand

        # --- Pagination Controls ---
        self.pagination_frame = ctk.CTkFrame(self.main_frame)
        self.pagination_frame.grid(row=8, column=0, columnspan=2, pady=(5, 0), sticky="ew")
        self.pagination_frame.grid_columnconfigure((0, 2), weight=1) # Center the label
        self.pagination_frame.grid_remove() # Hide initially

        self.prev_button = ctk.CTkButton(self.pagination_frame, text="< Previous", command=self.previous_page, state="disabled")
        self.prev_button.grid(row=0, column=0, sticky="e", padx=20)

        self.page_label = ctk.CTkLabel(self.pagination_frame, text="Page 1 / 1")
        self.page_label.grid(row=0, column=1, padx=20)

        self.next_button = ctk.CTkButton(self.pagination_frame, text="Next >", command=self.next_page, state="disabled")
        self.next_button.grid(row=0, column=2, sticky="w", padx=20)

        # --- Loading Animation ---
        self.loading_frame = ctk.CTkFrame(self.main_frame)
        self.loading_label = ctk.CTkLabel(self.loading_frame, text="Generating combinations, please wait...", font=("Arial", 18))
        self.loading_label.pack(pady=20, padx=20)
        self.loading_animation_label = ctk.CTkLabel(self.loading_frame, text="", font=("Courier", 20))
        self.loading_animation_label.pack(pady=10)
        self.animation_chars = ["|", "/", "-", "\\"]
        self.animation_index = 0
        self._animation_job = None

        # --- Instruction Animation ---
        self.instruction_animation_job = None
        self.instruction_animation_chars = ["", ".", "..", "..."]
        self.instruction_animation_index = 0

        self.presets = {}
        self.load_presets()
        self.update_presets_menu()

        self.after(100, self.poll_queues)
        self.update_dist_filter_buttons() # Set initial button state
        self.change_language("English") # Set default language

    def change_language(self, language: str):
        self.current_language = "en" if language == "English" else "es"
        lang_dict = self.translations[self.current_language]

        self.label_interface.configure(text=lang_dict["select_interface"])
        self.label_category.configure(text=lang_dict["select_module_type"])
        self.rescreen_button.configure(text=lang_dict["refilter"])
        self.label_presets.configure(text=lang_dict.get("select_preset", "Select Preset:"))
        self.save_preset_button.configure(text=lang_dict.get("save", "💾 Save"))
        self.delete_preset_button.configure(text=lang_dict.get("delete", "🗑️ Delete"))
        
        self.update_dynamic_instruction()
        
        # Update instruction text if it's currently visible
        if self.instruction_label_simple.winfo_viewable():
            if "Waiting" in self.base_instruction_text:
                 self.base_instruction_text = lang_dict["waiting_for_modules"]
            elif "Change channels" in self.base_instruction_text:
                 self.base_instruction_text = lang_dict["change_channel_instruction"]
            self.instruction_label_simple.configure(text=self.base_instruction_text)


    def update_dynamic_instruction(self):
        # Clear previous widgets
        for widget in self.instruction_text_frame.winfo_children():
            widget.destroy()

        lang_dict = self.translations[self.current_language]
        
        ctk.CTkLabel(self.instruction_text_frame, text=lang_dict["dynamic_instruction_1"], font=("Segoe UI", 14)).pack(side="left")
        ctk.CTkLabel(self.instruction_text_frame, text="Start Monitoring", font=("Segoe UI", 14, "bold"), fg_color="#1F6AA5", corner_radius=5).pack(side="left", padx=4)
        ctk.CTkLabel(self.instruction_text_frame, text=lang_dict["dynamic_instruction_2"], font=("Segoe UI", 14)).pack(side="left")


    def load_font_awesome(self) -> Optional[CTkFont]:
        """Loads the Font Awesome font if available."""
        font_path = "Font Awesome 7 Free-Solid-900.otf"
        if os.path.exists(font_path):
            try:
                # Load the base font for normal text
                base_font_info = ctk.CTkFont(family="Segoe UI", size=12)
                # Create a new font that mixes the base with Font Awesome
                fa_font = CTkFont(family=base_font_info.cget("family"), size=14)
                # CustomTkinter does not officially support loading fonts by path,
                # but by registering it with Tkinter, it should be available.
                # This is a workaround.
                self.tk.call("font", "create", "FontAwesome", "-family", "FontAwesome", "-size", "14")
                
                # The button text can now use a mix of fonts.
                # For the icons, we will use the Unicode characters directly.
                # We return a font with a suitable size for the buttons.
                return CTkFont(family="Segoe UI", size=14)
            except Exception as e:
                logging.error(f"Could not load Font Awesome font: {e}")
                return None
        else:
            logging.warning(f"Font Awesome file not found at '{font_path}'. Icons will not be displayed.")
            return None

    def load_module_images(self) -> Dict[str, ctk.CTkImage]:
        """Loads all module images from the Modulos directory."""
        images = {}
        image_dir = "Modulos"
        if not os.path.isdir(image_dir):
            logging.warning(f"Image directory '{image_dir}' not found.")
            return images
        
        for filename in os.listdir(image_dir):
            if filename.endswith(".webp"):
                try:
                    # Match names like "Epic Attack" from "Epic Attack.webp"
                    name = os.path.splitext(filename)[0]
                    filepath = os.path.join(image_dir, filename)
                    img = Image.open(filepath).resize((60, 60), Image.Resampling.LANCZOS)
                    images[name] = ctk.CTkImage(light_image=img, dark_image=img, size=(60, 60))
                except Exception as e:
                    logging.error(f"Failed to load image {filename}: {e}")
        return images

    def load_attribute_images(self) -> Dict[str, ctk.CTkImage]:
        """Loads all attribute icon images from the Module-Effects directory."""
        images = {}
        image_dir = "Module-Effects"
        if not os.path.isdir(image_dir):
            logging.warning(f"Image directory '{image_dir}' not found.")
            return images
        
        for filename in os.listdir(image_dir):
            if filename.endswith(".webp"):
                try:
                    # Match names like "Armor" from "Armor.webp"
                    name = os.path.splitext(filename)[0]
                    filepath = os.path.join(image_dir, filename)
                    img = Image.open(filepath).resize((18, 18), Image.Resampling.LANCZOS)
                    images[name] = ctk.CTkImage(light_image=img, dark_image=img, size=(18, 18))
                except Exception as e:
                    logging.error(f"Failed to load attribute icon {filename}: {e}")
        return images

    def toggle_console(self):
        if self.console_frame.winfo_viewable():
            self.console_frame.grid_remove()
            self.toggle_console_button.configure(text=">")
            self.grid_columnconfigure(1, weight=0)
        else:
            self.console_frame.grid()
            self.toggle_console_button.configure(text="<")
            self.grid_columnconfigure(1, weight=1)

    def toggle_filters(self):
        if self.filters_frame.winfo_viewable():
            self.filters_frame.grid_remove()
        else:
            self.filters_frame.grid()

    def toggle_attribute(self, attribute_name: str):
        """Toggles the selection state of an attribute button."""
        if attribute_name in self.selected_attributes:
            self.selected_attributes.remove(attribute_name)
            self.attribute_buttons[attribute_name].configure(fg_color="#2C2E33")
        else:
            self.selected_attributes.add(attribute_name)
            self.attribute_buttons[attribute_name].configure(fg_color="#1F6AA5") # Blue

        # Update "All" button state
        if len(self.selected_attributes) == len(self.all_attributes):
            self.attribute_buttons["All"].configure(fg_color="#1F6AA5")
        else:
            self.attribute_buttons["All"].configure(fg_color="#2C2E33")

    def toggle_all_attributes(self):
        """Toggles all attributes on or off."""
        if len(self.selected_attributes) == len(self.all_attributes):
            # If all are selected, deselect all
            self.selected_attributes.clear()
            for attr, button in self.attribute_buttons.items():
                button.configure(fg_color="#2C2E33")
        else:
            # If not all are selected, select all
            self.selected_attributes.update(self.all_attributes)
            for attr, button in self.attribute_buttons.items():
                if attr != "All":
                    button.configure(fg_color="#1F6AA5")
            self.attribute_buttons["All"].configure(fg_color="#1F6AA5")

    def poll_queues(self):
        # Merge processing of two queues
        # Process log queue
        while True:
            try:
                record = self.log_queue.get(block=False)
                self.log_textbox.configure(state="normal")
                self.log_textbox.insert("end", record)
                self.log_textbox.see("end")
                self.log_textbox.configure(state="disabled")

                # Check for specific log message to update instructions
                if "识别到游戏服务器" in record:
                    self.instruction_text_frame.pack_forget()
                    if not self.instruction_label_simple.winfo_viewable():
                        self.instruction_label_simple.pack(side="left", padx=(0, 10), pady=5)
                    
                    self.instruction_icon.configure(text="🔄", text_color="#1E90FF") # Blue sync icon
                    self.base_instruction_text = self.translations[self.current_language]["waiting_for_modules"]
                    self.instruction_label_simple.configure(text=self.base_instruction_text)
                    self.start_instruction_animation()
            except queue.Empty:
                break
        
        # Process progress queue
        while True:
            try:
                message = self.progress_queue.get(block=False)
                self.status_label.configure(text=f"Status: {message}")
            except queue.Empty:
                break
        
        # Process results queue
        while True:
            try:
                results = self.results_queue.get(block=False)
                self.update_results_display(results)
            except queue.Empty:
                break
                
        self.after(100, self.poll_queues)

    def progress_callback(self, message: str):
        """Thread-safely puts a progress message into the queue."""
        self.progress_queue.put(message)

    def results_callback(self, results: List[Any]):
        """Thread-safely puts optimization results into the queue."""
        self.results_queue.put(results)

    def next_page(self):
        if self.current_page < (len(self.solutions_cache) - 1) // self.results_per_page:
            self.current_page += 1
            self.display_current_page()

    def previous_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.display_current_page()

    def update_results_display(self, solutions: List[Any]):
        """Caches results, applies filters, and displays the first page."""
        self.stop_animation()
        self.stop_instruction_animation()
        self.loading_frame.grid_remove()
        self.results_frame.grid()
        self.pagination_frame.grid()
        self.instruction_frame.grid_remove() # Hide instructions
        self.dist_filter_frame.grid() # Show distribution filter

        self.all_solutions_cache = solutions
        self.apply_filters_and_redisplay()

    def display_current_page(self):
        """Clears and rebuilds the results display for the current page."""
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        if not self.solutions_cache:
            self.pagination_frame.grid_remove()
            no_results_label = ctk.CTkLabel(self.results_frame, text="No valid combinations found.", font=("Segoe UI", 16))
            no_results_label.pack(pady=20)
            return

        total_pages = (len(self.solutions_cache) - 1) // self.results_per_page + 1
        self.page_label.configure(text=f"Page {self.current_page + 1} / {total_pages}")

        self.prev_button.configure(state="normal" if self.current_page > 0 else "disabled")
        self.next_button.configure(state="normal" if self.current_page < total_pages - 1 else "disabled")

        start_index = self.current_page * self.results_per_page
        end_index = start_index + self.results_per_page
        page_solutions = self.solutions_cache[start_index:end_index]

        rarity_colors = {
            "Rare": "#34558b",
            "Epic": "#6f42c1",
            "Legendary": "#ffc107"
        }

        for i, solution in enumerate(page_solutions):
            rank = start_index + i + 1
            row, col = divmod(i, 2)

            solution_frame = ctk.CTkFrame(self.results_frame, border_width=2, border_color="#565B5E")
            solution_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            solution_frame.grid_columnconfigure(0, weight=1)

            header_frame = ctk.CTkFrame(solution_frame, fg_color="transparent")
            header_frame.grid(row=0, column=0, padx=10, pady=(5, 10), sticky="ew")
            header_frame.grid_columnconfigure(0, weight=1)
            header_frame.grid_columnconfigure(1, weight=1)

            left_header_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
            left_header_frame.grid(row=0, column=0, sticky="w")

            header_label = ctk.CTkLabel(
                left_header_frame, 
                text=f"Rank {rank} (Score: {solution.optimization_score:.2f})",
                font=("Segoe UI", 16, "bold")
            )
            header_label.pack(side="left")

            right_header_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
            right_header_frame.grid(row=0, column=1, sticky="e")

            total_attr_value = sum(solution.attr_breakdown.values())
            
            # The combat power is stored in the 'score' attribute of the solution.
            combat_power = getattr(solution, 'score', 'N/A') 
            if isinstance(combat_power, (int, float)):
                combat_power = f"{combat_power:.0f}"

            stats_text = f"Total Attributes: {total_attr_value} | Hability Score: {combat_power}"
            stats_label = ctk.CTkLabel(
                right_header_frame,
                text=stats_text,
                font=("Segoe UI", 12)
            )
            stats_label.pack(side="right")

            content_frame = ctk.CTkFrame(solution_frame, fg_color="transparent")
            content_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
            content_frame.grid_columnconfigure(0, weight=1)

            modules_container = ctk.CTkFrame(content_frame, fg_color="transparent")
            modules_container.grid(row=0, column=0, pady=5, sticky="nsew")
            
            for j, module in enumerate(solution.modules):
                modules_container.grid_columnconfigure(j, weight=1)
                rarity = module.name.split()[0]
                color = rarity_colors.get(rarity, "#333333")

                module_card = ctk.CTkFrame(modules_container, border_width=1, border_color="gray", fg_color=color)
                module_card.grid(row=0, column=j, padx=5, pady=5, sticky="ns")

                img_label = ctk.CTkLabel(module_card, image=self.module_images.get(module.name), text="")
                img_label.pack(pady=(5, 5), padx=5)
                
                attrs_frame = ctk.CTkFrame(module_card, fg_color="transparent")
                attrs_frame.pack(pady=5, padx=5, anchor="w", fill="x")

                for part in module.parts:
                    attr_line_frame = ctk.CTkFrame(attrs_frame, fg_color="transparent")
                    attr_line_frame.pack(anchor="w")
                    
                    icon = self.attribute_images.get(part.name)
                    if icon:
                        icon_label = ctk.CTkLabel(attr_line_frame, image=icon, text="")
                        icon_label.pack(side="left", padx=(0, 3))

                    attr_text = f"{part.name}+{part.value}"
                    attrs_label = ctk.CTkLabel(attr_line_frame, text=attr_text, font=("Segoe UI", 10))
                    attrs_label.pack(side="left")

            stats_frame = ctk.CTkFrame(content_frame)
            stats_frame.grid(row=1, column=0, pady=5, sticky="nsew")

            ctk.CTkLabel(stats_frame, text="Attribute Distribution:", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=10, pady=(5, 2))
            
            attr_dist_frame = ctk.CTkFrame(stats_frame, fg_color="transparent")
            attr_dist_frame.pack(anchor="w", padx=10, pady=2, fill="x")

            # Sort attributes by value (Lv) in descending order
            for attr_name, value in sorted(solution.attr_breakdown.items(), key=lambda item: item[1], reverse=True):
                level_str = "(Lv.0)"
                if value >= 20: level_str = "(Lv.6)"
                elif value >= 16: level_str = "(Lv.5)"
                elif value >= 12: level_str = "(Lv.4)"
                elif value >= 8: level_str = "(Lv.3)"
                elif value >= 4: level_str = "(Lv.2)"
                elif value >= 1: level_str = "(Lv.1)"
                
                attr_line_frame = ctk.CTkFrame(attr_dist_frame, fg_color="transparent")
                attr_line_frame.pack(anchor="w", fill="x")

                icon = self.attribute_images.get(attr_name)
                if icon:
                    icon_label = ctk.CTkLabel(attr_line_frame, image=icon, text="")
                    icon_label.pack(side="left", padx=(0, 3))

                attr_dist_text = f"{attr_name} {level_str}: +{value}"
                ctk.CTkLabel(attr_line_frame, text=attr_dist_text, font=("Segoe UI", 11), justify="left").pack(side="left")

    def set_distribution_filter(self, filter_name: str):
        """Sets the distribution filter and re-applies it to the cached results."""
        self.distribution_filter = filter_name
        self.update_dist_filter_buttons()
        logging.info(f"Distribution filter set to: {filter_name}")
        self.apply_filters_and_redisplay()

    def update_dist_filter_buttons(self):
        """Updates the appearance of distribution filter buttons."""
        # This color should ideally be from the theme, but this is a simple way
        selected_color = "#1F6AA5" # A blue color from the default theme
        default_color = ctk.ThemeManager.theme["CTkButton"]["fg_color"]
        
        for name, button in self.dist_filter_buttons.items():
            if name == self.distribution_filter:
                button.configure(fg_color=selected_color)
            else:
                button.configure(fg_color=default_color)

    def apply_filters_and_redisplay(self):
        """Filters the all_solutions_cache based on current filters and updates the display."""
        if not self.all_solutions_cache:
            self.solutions_cache = []
            self.display_current_page() # Show "No results"
            return

        if self.distribution_filter == "All":
            filtered_solutions = self.all_solutions_cache
        else:
            filtered_solutions = []
            for solution in self.all_solutions_cache:
                lv5_count = 0
                lv6_count = 0
                for value in solution.attr_breakdown.values():
                    if value >= 20:
                        lv6_count += 1
                    elif value >= 16:
                        lv5_count += 1
                
                match = False
                if self.distribution_filter == "Lv.5" and lv5_count >= 1 and lv6_count == 0:
                    match = True
                elif self.distribution_filter == "Lv.5/Lv.5" and lv5_count >= 2:
                    match = True
                elif self.distribution_filter == "Lv.5/Lv.6" and lv5_count >= 1 and lv6_count >= 1:
                    match = True
                elif self.distribution_filter == "Lv.6/Lv.6" and lv6_count >= 2:
                    match = True
                
                if match:
                    filtered_solutions.append(solution)

        self.solutions_cache = filtered_solutions
        self.current_page = 0
        self.display_current_page()

    def start_animation(self):
        """Starts the text-based loading animation."""
        if self._animation_job:
            return
        self.animation_index = 0
        self._animate()

    def _animate(self):
        """Helper function to update the animation frame."""
        self.loading_animation_label.configure(text=self.animation_chars[self.animation_index])
        self.animation_index = (self.animation_index + 1) % len(self.animation_chars)
        self._animation_job = self.after(100, self._animate)

    def stop_animation(self):
        """Stops the loading animation."""
        if self._animation_job:
            self.after_cancel(self._animation_job)
            self._animation_job = None

    def start_instruction_animation(self):
        """Starts the text-based instruction animation."""
        if self.instruction_animation_job:
            return
        self.instruction_animation_index = 0
        self._animate_instruction()

    def _animate_instruction(self):
        """Helper function to update the instruction animation frame."""
        dots = self.instruction_animation_chars[self.instruction_animation_index]
        self.instruction_label_simple.configure(text=f"{self.base_instruction_text}{dots}")
        self.instruction_animation_index = (self.instruction_animation_index + 1) % len(self.instruction_animation_chars)
        self.instruction_animation_job = self.after(500, self._animate_instruction)

    def stop_instruction_animation(self):
        """Stops the instruction animation."""
        if self.instruction_animation_job:
            self.after_cancel(self.instruction_animation_job)
            self.instruction_animation_job = None

    def load_presets(self):
        try:
            with open("custom_presets.json", "r") as f:
                self.presets = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.presets = {"Manual Input / Clear": ""} # Default
            self.save_presets_to_file()

    def save_presets_to_file(self):
        with open("custom_presets.json", "w") as f:
            json.dump(self.presets, f, indent=4)

    def update_presets_menu(self):
        self.presets_menu.configure(values=list(self.presets.keys()))
        self.presets_menu.set("Manual Input / Clear")

    def apply_preset(self, preset_name: str):
        attributes_str = self.presets.get(preset_name, "")
        preset_attributes = set()
        if attributes_str:
            # Split the string by commas and then strip whitespace from each attribute
            temp_attributes = [attr.strip() for attr in attributes_str.split(",") if attr.strip()]
            for attr in temp_attributes:
                if attr in self.all_attributes:
                    preset_attributes.add(attr)

        # Deselect all currently selected attributes
        for attr in list(self.selected_attributes):
            if attr in self.attribute_buttons:
                self.toggle_attribute(attr)

        # Select attributes from the preset
        for attr in preset_attributes:
            if attr in self.attribute_buttons:
                self.toggle_attribute(attr)

    def save_preset(self):
        lang_dict = self.translations[self.current_language]
        title = lang_dict.get("save_preset_title", "Save Preset")
        prompt = lang_dict.get("save_preset_prompt", "Enter a name for the current attribute selection:")
        
        dialog = ctk.CTkInputDialog(text=prompt, title=title)
        self.attributes("-topmost", False)
        preset_name = dialog.get_input()
        self.attributes("-topmost", True)

        if preset_name and preset_name not in self.presets:
            # Join attributes with a comma and space
            current_attributes = ", ".join(sorted(list(self.selected_attributes)))
            self.presets[preset_name] = current_attributes
            self.save_presets_to_file()
            self.update_presets_menu()
            self.presets_menu.set(preset_name)

    def delete_preset(self):
        preset_name = self.presets_menu.get()
        if preset_name == "Manual Input / Clear":
            return # Cannot delete the default
        
        lang_dict = self.translations[self.current_language]
        title = lang_dict.get("delete_preset_title", "Delete Preset")
        prompt = lang_dict.get("delete_preset_prompt", "Are you sure you want to delete the preset '{preset_name}'?").format(preset_name=preset_name)

        if tkinter.messagebox.askyesno(title, prompt):
            if preset_name in self.presets:
                del self.presets[preset_name]
                self.save_presets_to_file()
                self.update_presets_menu()

    def start_monitoring(self):
        selected_interface_display = self.interface_menu.get()
        if not selected_interface_display:
            logging.error("Error: Please select a network interface first!")
            return
        
        interface_name = self.interface_map[selected_interface_display]
        category = self.category_menu.get()
        attributes = list(self.selected_attributes)

        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        self.log_textbox.insert("end", "After pressing the start button and choosing the filter, please switch channels in the game in a place with few players around you.\n\n")
        self.log_textbox.configure(state="disabled")
        self.status_label.configure(text="Status: Starting monitoring...")
        
        # Update instruction label
        self.instruction_text_frame.pack_forget()
        self.instruction_label_simple.pack(side="left", padx=(0, 10), pady=5)
        self.instruction_icon.configure(text="⚠️", text_color="#FFA500") # Orange warning
        self.base_instruction_text = self.translations[self.current_language]["change_channel_instruction"]
        self.instruction_label_simple.configure(text=self.base_instruction_text)
        self.instruction_frame.grid()

        # Clear previous results and cache
        self.solutions_cache = []
        self.current_page = 0
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        self.pagination_frame.grid_remove()

        self.monitor_instance = StarResonanceMonitor(
            interface_name=interface_name,
            category=category,
            attributes=attributes,
            on_data_captured_callback=self.enable_rescreening,
            progress_callback=self.progress_callback,
            on_results_callback=self.results_callback # Pass results callback
        )
        
        self.monitor_thread = threading.Thread(target=self.monitor_instance.start_monitoring, daemon=True)
        self.monitor_thread.start()

        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.interface_menu.configure(state="disabled")
        self.category_menu.configure(state="normal")
        self.rescreen_button.configure(state="disabled")
        self.status_label.configure(text="Status: Monitoring game data...")

    def stop_monitoring(self):
        if self.monitor_instance:
            self.monitor_instance.stop_monitoring()
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=1.0)

        self.monitor_instance = None
        self.monitor_thread = None

        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.interface_menu.configure(state="normal")
        self.rescreen_button.configure(state="disabled")
        self.status_label.configure(text="Status: Idle")
        self.dist_filter_frame.grid_remove() # Hide distribution filter
        self.stop_instruction_animation()

        # Reset instruction label to initial state
        self.instruction_label_simple.pack_forget()
        self.update_dynamic_instruction() # Re-create the initial instruction in the correct language
        self.instruction_text_frame.pack(side="left", padx=(0, 10), pady=5)
        self.instruction_icon.configure(text="⚠️", text_color="#FFCC00") # Yellow warning
        self.instruction_frame.grid()

    def rescreen_results(self):
        """Rescreens existing data"""
        if not self.monitor_instance or not self.monitor_instance.has_captured_data():
            logging.warning("No captured module data available for rescreening.")
            return

        # Clear cache and show loading animation
        self.solutions_cache = []
        self.current_page = 0
        self.pagination_frame.grid_remove()
        self.results_frame.grid_remove()
        self.instruction_frame.grid_remove() # Hide instructions
        self.loading_frame.grid(row=8, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        self.start_animation()
        
        category = self.category_menu.get()
        attributes = list(self.selected_attributes)
        
        logging.info("=== User requested rescreening with new conditions... ===")
        
        threading.Thread(
            target=self.monitor_instance.rescreen_modules,
            args=(category, attributes),
            daemon=True
        ).start()
    
    def enable_rescreening(self):
        """Callback function to enable the "Rescreen" button"""
        self.rescreen_button.configure(state="normal")
        self.status_label.configure(text="Status: Data captured, ready to rescreen.")
        
    def on_closing(self):
        self.stop_monitoring()
        self.destroy()

if __name__ == "__main__":
    import multiprocessing
    # Add multiprocessing support for packaging tools like PyInstaller
    multiprocessing.freeze_support() 
    
    setup_logging(debug_mode=True)
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("dark-blue")
    app = App()
    app.mainloop()

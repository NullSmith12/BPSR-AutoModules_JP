# gui_app.py

import tkinter
from tkinter import filedialog, simpledialog
import customtkinter as ctk
from customtkinter import CTkFont
import threading
from typing import Optional, Dict, List, Any
import queue
import logging
import sys
import os
import json
from pathlib import Path
from PIL import Image

from localization import (
    DEFAULT_LANGUAGE,
    DISTRIBUTION_FILTER_ORDER,
    get_app_translations,
    get_attribute_label,
    get_canonical_category,
    get_category_label,
    get_category_options,
    get_distribution_filter_label,
    get_language_code,
    get_language_label,
    get_language_options,
    get_preset_display_name,
)
from module_csv_io import export_modules_to_csv, import_modules_from_csv
from network_interface_util import get_network_interfaces
from star_resonance_monitor_core import StarResonanceMonitor
from logging_config import setup_logging

APP_BASE_DIR = Path(__file__).resolve().parent


def get_resource_base_dir() -> Path:
    """同梱済みリソースの配置先を返す。"""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return APP_BASE_DIR


def get_user_data_dir() -> Path:
    """ユーザーが更新するデータの保存先を返す。"""
    if getattr(sys, "frozen", False):
        root = os.environ.get("LOCALAPPDATA")
        if root:
            path = Path(root) / "BPSR-AutoModules"
        else:
            path = Path.home() / ".bpsr_automodules"
        path.mkdir(parents=True, exist_ok=True)
        return path

    return APP_BASE_DIR

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

        self.resource_base_dir = get_resource_base_dir()
        self.user_data_dir = get_user_data_dir()
        self.presets_file_path = self.user_data_dir / "custom_presets.json"

        # --- TEMA ---
        self.THEME = {
            "color": {
                "background_main": "#202124",      # Fondo principal (muy oscuro)
                "background_secondary": "#303134", # Paneles, botones inactivos
                "text_primary": "#E8EAED",         # Texto principal (blanco roto)
                "text_secondary": "#9AA0A6",       # Texto de placeholder o secundario
                "border": "#5F6368",               # Bordes sutiles
                "button_active_bg": "#E8EAED",     # Fondo de botón activo (el color del texto)
                "button_active_text": "#202124"    # Texto de botón activo (el color del fondo)
            },
            "font": {
                "main": ("Segoe UI", 14),
                "title": ("Segoe UI", 24, "bold"),
                "subtitle": ("Segoe UI", 16, "bold"),
                "small": ("Segoe UI", 12)
            }
        }
        # --- FIN DE TEMA ---
        
        self.title("BPSR モジュール最適化ツール 日本語版")
        # Aplicar color de fondo a la ventana principal
        self.configure(fg_color=self.THEME["color"]["background_main"])
        self._apply_window_icon()
        self.attributes("-topmost", True)
        self.geometry("1100x1070")
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

        self.main_frame = ctk.CTkFrame(self, fg_color="transparent") # Hazlo transparente para que se vea el fondo de la ventana
        self.main_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1) # Columna para el frame de botones de control (izquierda)
        self.main_frame.grid_columnconfigure(1, weight=1) # Columna para el frame de instrucciones (derecha)

        # --- Language Selection ---
        self.translations = get_app_translations()
        for language, extra_texts in {
            "ja": {
                "window_title": "BPSR モジュール最適化ツール 日本語版",
                "app_title": "BPSR モジュール最適化ツール",
                "priority_limit_warning": "優先属性は最大6件までです。",
                "select_interface_first": "先にネットワークインターフェースを選択してください。",
                "no_rescreen_data": "最適化に使えるモジュールデータがありません。",
                "start_optimization": "最適化開始",
                "import_csv": "CSV読込",
                "export_csv": "CSV保存",
                "csv_import_title": "モジュール CSV を読み込む",
                "csv_export_title": "モジュール CSV を保存する",
                "csv_import_success": "{count} 件のモジュールを CSV から読み込みました。",
                "csv_export_success": "{count} 件のモジュールを CSV に保存しました。",
                "csv_import_failed": "CSV の読み込みに失敗しました: {error}",
                "csv_export_failed": "CSV の保存に失敗しました: {error}",
                "no_export_data": "CSV に保存できるモジュールデータがありません。",
                "stop_monitoring_before_import": "CSV を読み込む前に監視を停止してください。",
                "captured_data_waiting_stop": "モジュール一覧を取得しました。監視停止後に最適化を実行できます。",
                "data_captured_ready": "モジュール一覧を保持しました。最適化開始を押してください。",
                "rescreen_requested": "=== 現在の条件で最適化を開始します ===",
            },
            "en": {
                "window_title": "BPSR Module Optimizer 日本語版",
                "app_title": "BPSR Module Optimizer",
                "priority_limit_warning": "Cannot add more than 6 prioritized attributes.",
                "select_interface_first": "Please select a network interface first.",
                "no_rescreen_data": "No captured module data available for optimization.",
                "start_optimization": "Optimize",
                "import_csv": "Import CSV",
                "export_csv": "Export CSV",
                "csv_import_title": "Import module CSV",
                "csv_export_title": "Export module CSV",
                "csv_import_success": "Loaded {count} modules from CSV.",
                "csv_export_success": "Saved {count} modules to CSV.",
                "csv_import_failed": "Failed to import CSV: {error}",
                "csv_export_failed": "Failed to export CSV: {error}",
                "no_export_data": "No module data available for CSV export.",
                "stop_monitoring_before_import": "Stop monitoring before importing a CSV file.",
                "captured_data_waiting_stop": "Module list captured. Stop monitoring to run optimization.",
                "data_captured_ready": "Module list retained. Press Optimize to run calculations.",
                "rescreen_requested": "=== Starting optimization with current conditions... ===",
            },
            "es": {
                "window_title": "BPSR Module Optimizer 日本語版",
                "app_title": "BPSR Module Optimizer",
                "priority_limit_warning": "No se pueden priorizar más de 6 atributos.",
                "select_interface_first": "Primero selecciona una interfaz de red.",
                "no_rescreen_data": "No hay datos capturados para optimizar.",
                "start_optimization": "Optimizar",
                "import_csv": "Importar CSV",
                "export_csv": "Exportar CSV",
                "csv_import_title": "Importar CSV de módulos",
                "csv_export_title": "Exportar CSV de módulos",
                "csv_import_success": "Se cargaron {count} módulos desde el CSV.",
                "csv_export_success": "Se guardaron {count} módulos en el CSV.",
                "csv_import_failed": "No se pudo importar el CSV: {error}",
                "csv_export_failed": "No se pudo exportar el CSV: {error}",
                "no_export_data": "No hay datos de módulos para exportar a CSV.",
                "stop_monitoring_before_import": "Detén la monitorización antes de importar un CSV.",
                "captured_data_waiting_stop": "Lista de módulos capturada. Detén la monitorización para optimizar.",
                "data_captured_ready": "La lista de módulos se ha conservado. Pulsa Optimizar para calcular.",
                "rescreen_requested": "=== Iniciando optimización con las condiciones actuales... ===",
            },
        }.items():
            self.translations.setdefault(language, {}).update(extra_texts)
        self.current_language = DEFAULT_LANGUAGE
        self.current_status_key = "idle"
        self.current_status_message = self.translations[self.current_language]["idle"]
        self.base_instruction_key = "change_channel_instruction"
        self.base_instruction_text = self.translations[self.current_language][self.base_instruction_key]
        self.default_preset_key = "Manual Input / Clear"
        self.preset_display_to_key: Dict[str, str] = {}

        # --- Title Frame ---
        title_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        title_frame.grid(row=0, column=0, columnspan=2, pady=(5, 2), sticky="ew", padx=5)
        title_frame.grid_columnconfigure(0, weight=1)
        title_frame.grid_columnconfigure(1, weight=0)

        title_left_frame = ctk.CTkFrame(title_frame, fg_color="transparent")
        title_left_frame.grid(row=0, column=0, sticky="w")

        app_icon_img = ctk.CTkImage(Image.open(self.get_resource_path("icon.png")), size=(40, 40))
        app_icon = ctk.CTkLabel(title_left_frame, image=app_icon_img, text="")
        app_icon.pack(side="left", padx=(0, 10))

        self.title_label = ctk.CTkLabel(title_left_frame, text=self.tr("app_title"), 
                                font=self.THEME["font"]["title"], 
                                text_color=self.THEME["color"]["text_primary"])
        self.title_label.pack(side="left")

        self.language_menu = ctk.CTkOptionMenu(title_left_frame, values=get_language_options(), command=self.change_language)
        self.language_menu.pack(side="left", padx=10)
        self.language_menu.set(get_language_label(self.current_language))

        # --- Filter Frame (initially visible) ---
        self.filters_frame = ctk.CTkFrame(self.main_frame, fg_color=self.THEME["color"]["background_secondary"], corner_radius=15)
        self.filters_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")
        # Reconfiguración de columnas para self.filters_frame
        self.filters_frame.grid_columnconfigure(0, weight=1) # Columna para Category
        self.filters_frame.grid_columnconfigure(1, weight=1) # Columna para Category Menu
        self.filters_frame.grid_columnconfigure(2, weight=1) # Columna para Interface Label
        self.filters_frame.grid_columnconfigure(3, weight=1) # Columna para Interface Menu
        self.filters_frame.grid_columnconfigure(4, weight=1) # Nueva columna para priority_ordering_frame

        # Column 0
        self.label_category = ctk.CTkLabel(self.filters_frame, text=self.tr("select_module_type"), 
                                   font=self.THEME["font"]["main"],
                                   text_color=self.THEME["color"]["text_primary"])
        self.label_category.grid(row=0, column=0, padx=5, pady=(5, 2), sticky="w")
        self.category_menu = ctk.CTkOptionMenu(
            self.filters_frame, values=get_category_options(self.current_language),
            fg_color=self.THEME["color"]["background_main"], # Fondo interior
            button_color=self.THEME["color"]["background_secondary"], # Color del botón
            button_hover_color=self.THEME["color"]["border"],
            text_color=self.THEME["color"]["text_primary"],
            dropdown_fg_color=self.THEME["color"]["background_secondary"],
            dropdown_hover_color=self.THEME["color"]["border"],
            corner_radius=8
        )
        self.category_menu.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        self.category_menu.set(get_category_label("All", self.current_language))
        self.category_menu.configure(state="normal") # Ensure it\'s enabled initially

        self.label_interface = ctk.CTkLabel(self.filters_frame, text=self.tr("select_interface"),
                                    font=self.THEME["font"]["main"],
                                    text_color=self.THEME["color"]["text_primary"])
        self.label_interface.grid(row=0, column=2, padx=5, pady=(5, 2), sticky="w")
        self.interface_menu = ctk.CTkOptionMenu(
            self.filters_frame, values=list(self.interface_map.keys()),
            fg_color=self.THEME["color"]["background_main"],
            button_color=self.THEME["color"]["background_secondary"],
            button_hover_color=self.THEME["color"]["border"],
            text_color=self.THEME["color"]["text_primary"],
            dropdown_fg_color=self.THEME["color"]["background_secondary"],
            dropdown_hover_color=self.THEME["color"]["border"],
            corner_radius=8
        )
        self.interface_menu.grid(row=0, column=3, padx=5, pady=2, sticky="ew")

        # --- Presets Frame ---
        self.presets_frame = ctk.CTkFrame(self.filters_frame, fg_color=self.THEME["color"]["background_secondary"], corner_radius=15)
        self.presets_frame.grid(row=1, column=0, columnspan=4, padx=5, pady=(5,0), sticky="ew")
        self.presets_frame.grid_columnconfigure(0, weight=0)
        self.presets_frame.grid_columnconfigure(1, weight=1)
        self.presets_frame.grid_columnconfigure(2, weight=0)
        self.presets_frame.grid_columnconfigure(3, weight=0)

        self.label_presets = ctk.CTkLabel(self.presets_frame, text=self.tr("select_preset"),
                                   font=self.THEME["font"]["main"],
                                   text_color=self.THEME["color"]["text_primary"])
        self.label_presets.grid(row=0, column=0, padx=(5, 2), pady=2, sticky="w")

        self.presets_menu = ctk.CTkOptionMenu(
            self.presets_frame, command=self.apply_preset,
            fg_color=self.THEME["color"]["background_main"],
            button_color=self.THEME["color"]["background_secondary"],
            button_hover_color=self.THEME["color"]["border"],
            text_color=self.THEME["color"]["text_primary"],
            dropdown_fg_color=self.THEME["color"]["background_secondary"],
            dropdown_hover_color=self.THEME["color"]["border"],
            corner_radius=8
        )
        self.presets_menu.grid(row=0, column=1, padx=2, pady=2, sticky="ew")

        self.save_preset_button = ctk.CTkButton(self.presets_frame, text="", command=self.save_preset, width=80, corner_radius=15, 
                                                fg_color=self.THEME["color"]["background_secondary"], 
                                                text_color=self.THEME["color"]["text_primary"],
                                                hover_color=self.THEME["color"]["border"],
                                                border_width=0)
        self.save_preset_button.grid(row=0, column=2, padx=2, pady=2)

        self.delete_preset_button = ctk.CTkButton(self.presets_frame, text="", command=self.delete_preset, width=80, corner_radius=15, 
                                                  fg_color=self.THEME["color"]["background_secondary"], 
                                                  text_color=self.THEME["color"]["text_primary"],
                                                  hover_color=self.THEME["color"]["border"],
                                                  border_width=0)
        self.delete_preset_button.grid(row=0, column=3, padx=2, pady=2)

        self.attributes_buttons_frame = ctk.CTkFrame(self.filters_frame, fg_color="transparent")
        # Asegurarse de que las 5 columnas internas no se estiren
        for i in range(5): # Para 5 columnas lógicas (0 a 4)
            self.attributes_buttons_frame.grid_columnconfigure(i, weight=0)

        # Mover attributes_buttons_frame a la fila 2 para eliminar el espacio de la advertencia
        self.attributes_buttons_frame.grid(row=2, column=0, columnspan=4, padx=5, pady=5)

        self.all_attributes = [
            "DMG Stack", "Agile", "Life Condense", "First Aid", "Life Wave", "Life Steal", 
            "Team Luck & Crit", "Final Protection", "Strength Boost", "Agility Boost", 
            "Intellect Boost", "Special Attack", "Elite Strike", "Healing Boost", 
            "Healing Enhance", "Cast Focus", "Attack SPD", "Crit Focus", "Luck Focus", 
            "Resistance", "Armor"
        ]
        
        self.attribute_buttons: Dict[str, ctk.CTkButton] = {}
        self.selected_attributes = set() # Attributes selected in the pill buttons (order not important here)
        self.ordered_prioritized_attrs: List[str] = [] # Attributes selected for priority ordering (order is important)
        self.update_filter_status() # Initial call to set warning status
        
        # --- Create "All" button ---
        all_button = ctk.CTkButton(
            self.attributes_buttons_frame,
            text=self.tr("all"),
            command=self.toggle_all_attributes,
            fg_color=self.THEME["color"]["background_secondary"], # Color inactivo
            text_color=self.THEME["color"]["text_primary"],
            hover_color=self.THEME["color"]["border"], # Un color sutil para el hover
            border_width=1, # Borde blanco
            border_color="white", # Color del borde blanco
            corner_radius=8, # ¡Muy importante para la forma de píldora!
            font=self.THEME["font"]["small"] # Reduce la fuente
        )
        all_button.grid(row=0, column=0, padx=1, pady=1)
        self.attribute_buttons["All"] = all_button

        # --- Create attribute buttons ---
        row, col = 0, 1
        for attr in self.all_attributes:
            if col > 4:  # Ajusta el número de columnas a 5
                col = 0
                row += 1
            
            button = ctk.CTkButton(
                self.attributes_buttons_frame,
                text=self.get_display_attribute_name(attr),
                command=lambda a=attr: self.toggle_attribute(a),
                fg_color=self.THEME["color"]["background_secondary"], # Color inactivo
                text_color=self.THEME["color"]["text_primary"],
                hover_color=self.THEME["color"]["border"], # Un color sutil para el hover
            border_width=1, # Borde blanco
            border_color="white", # Color del borde blanco
            corner_radius=8, # ¡Muy importante para la forma de píldora!
            font=self.THEME["font"]["small"] # Reduce la fuente
        )
            button.grid(row=row, column=col, padx=1, pady=1)
            self.attribute_buttons[attr] = button
            col += 1

        # --- Priority Ordering Controls ---
        # Reubicar este frame para que aparezca a la derecha de los botones de atributos
        self.priority_ordering_frame = ctk.CTkFrame(self.filters_frame, fg_color=self.THEME["color"]["background_secondary"], corner_radius=15)
        self.priority_ordering_frame.grid(row=2, column=4, padx=5, pady=(5,0), sticky="nsew") # Colocar en la fila 2, columna 4
        self.priority_ordering_frame.grid_columnconfigure(0, weight=1)

        self.priority_order_checkbox = ctk.CTkCheckBox(
            self.priority_ordering_frame, 
            text=self.tr("enable_priority_ordering"), 
            font=self.THEME["font"]["main"],
            text_color=self.THEME["color"]["text_primary"],
            command=self.update_priority_attrs_ui
        )
        self.priority_order_checkbox.grid(row=0, column=0, padx=5, pady=2, sticky="w")

        self.priority_attrs_container = ctk.CTkFrame(self.priority_ordering_frame, fg_color="transparent")
        self.priority_attrs_container.grid(row=1, column=0, padx=2, pady=2, sticky="ew")
        self.priority_attrs_container.grid_columnconfigure(0, weight=1)
        # This container will hold the ordered list of attributes with up/down/remove buttons
        self.update_priority_attrs_ui() # Initial call to set visibility

        # Frame para los botones de control (Start, Stop, Optimize)
        self.control_buttons_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.control_buttons_frame.grid(row=5, column=0, padx=5, pady=5, sticky="w")

        play_icon = ctk.CTkImage(Image.open(self.get_resource_path("Icons", "play.png")), size=(16, 16))
        self.start_button = ctk.CTkButton(self.control_buttons_frame, text=self.tr("start_monitoring"), image=play_icon, command=self.start_monitoring,
                                  corner_radius=8, 
                                  fg_color="#1F6AA5") # Mantén el azul por ahora o cámbialo a un color de acento
        self.start_button.pack(side="left", padx=5)

        stop_icon = ctk.CTkImage(Image.open(self.get_resource_path("Icons", "stop.png")), size=(16, 16))
        self.stop_button = ctk.CTkButton(self.control_buttons_frame, text=self.tr("stop_monitoring"), image=stop_icon, command=self.stop_monitoring, state="disabled",
                                  corner_radius=8, 
                                  fg_color=self.THEME["color"]["background_secondary"],
                                  text_color=self.THEME["color"]["text_primary"],
                                  hover_color=self.THEME["color"]["border"],
                                  border_width=0)
        self.stop_button.pack(side="left", padx=5)
        
        self.rescreen_button = ctk.CTkButton(self.control_buttons_frame, text=self.tr("start_optimization"), command=self.start_optimization, state="disabled", font=self.fa_font,
                                  corner_radius=8, 
                                  fg_color=self.THEME["color"]["background_secondary"],
                                  text_color=self.THEME["color"]["text_primary"],
                                  hover_color=self.THEME["color"]["border"],
                                  border_width=1, # Borde blanco
                                  border_color="white") # Color del borde blanco
        self.rescreen_button.pack(side="left", padx=5)

        self.import_csv_button = ctk.CTkButton(
            self.control_buttons_frame,
            text=self.tr("import_csv"),
            command=self.import_modules_csv,
            corner_radius=8,
            fg_color=self.THEME["color"]["background_secondary"],
            text_color=self.THEME["color"]["text_primary"],
            hover_color=self.THEME["color"]["border"],
            border_width=1,
            border_color="white",
        )
        self.import_csv_button.pack(side="left", padx=5)

        self.export_csv_button = ctk.CTkButton(
            self.control_buttons_frame,
            text=self.tr("export_csv"),
            command=self.export_modules_csv,
            state="disabled",
            corner_radius=8,
            fg_color=self.THEME["color"]["background_secondary"],
            text_color=self.THEME["color"]["text_primary"],
            hover_color=self.THEME["color"]["border"],
            border_width=1,
            border_color="white",
        )
        self.export_csv_button.pack(side="left", padx=5)

        # --- Dynamic Instructions ---
        self.instruction_frame = ctk.CTkFrame(title_frame, fg_color=self.THEME["color"]["background_secondary"], corner_radius=15)
        self.instruction_frame.grid(row=0, column=1, padx=(10, 0), pady=0, sticky="e")
        
        self.instruction_icon = ctk.CTkLabel(self.instruction_frame, text="⚠️", font=("Segoe UI Emoji", 16), text_color="#FFCC00") # Yellow warning, reduced size
        self.instruction_icon.pack(side="left", padx=(5, 2), pady=2)

        # Frame for complex, multi-part instruction
        self.instruction_text_frame = ctk.CTkFrame(self.instruction_frame, fg_color="transparent")
        self.instruction_text_frame.pack(side="left", padx=(0, 5), pady=2)

        self.update_dynamic_instruction()

        # Label for simple, single-part instructions
        self.instruction_label_simple = ctk.CTkLabel(self.instruction_frame, text="", font=self.THEME["font"]["small"], text_color=self.THEME["color"]["text_primary"]) # Using THEME["font"]["small"]

        # --- Distribution Filter ---
        self.dist_filter_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.dist_filter_frame.grid(row=6, column=0, columnspan=2, padx=5, pady=(2, 0), sticky="ew")
        self.dist_filter_frame.grid_remove() # Hide initially

        self.label_dist_filter = ctk.CTkLabel(self.dist_filter_frame, text=self.tr("attr_distribution"),
                                      font=self.THEME["font"]["main"],
                                      text_color=self.THEME["color"]["text_primary"])
        self.label_dist_filter.pack(side="left", padx=(5, 5))

        self.dist_filter_buttons: Dict[str, ctk.CTkButton] = {}
        for f in DISTRIBUTION_FILTER_ORDER:
            btn = ctk.CTkButton(
                self.dist_filter_frame,
                text=get_distribution_filter_label(f, self.current_language),
                command=lambda name=f: self.set_distribution_filter(name),
                fg_color=self.THEME["color"]["background_secondary"],
                text_color=self.THEME["color"]["text_primary"],
                hover_color=self.THEME["color"]["border"],
                border_width=0,
                corner_radius=15
            )
            btn.pack(side="left", padx=2)
            self.dist_filter_buttons[f] = btn

        # --- Console Panel ---
        self.console_frame = ctk.CTkFrame(self, width=400)
        self.console_frame.grid(row=0, column=1, rowspan=2, padx=5, pady=5, sticky="ns")
        self.console_frame.grid_remove() # Hide by default

        self.console_frame.grid_rowconfigure(0, weight=1)
        self.console_frame.grid_columnconfigure(0, weight=1)

        self.console_frame = ctk.CTkFrame(self, width=400, fg_color=self.THEME["color"]["background_secondary"], corner_radius=15)
        self.console_frame.grid(row=0, column=1, rowspan=2, padx=5, pady=5, sticky="ns")
        self.console_frame.grid_remove() # Hide by default

        self.console_frame.grid_rowconfigure(0, weight=1)
        self.console_frame.grid_columnconfigure(0, weight=1)

        self.log_textbox = ctk.CTkTextbox(self.console_frame, 
                                  fg_color=self.THEME["color"]["background_main"], # Un fondo más oscuro para el texto
                                  border_color=self.THEME["color"]["border"],
                                  border_width=1,
                                  text_color=self.THEME["color"]["text_primary"],
                                  font=self.THEME["font"]["main"])
        self.log_textbox.grid(row=0, column=0, padx=2, pady=2, sticky="nsew")

        # --- Status Bar ---
        self.status_frame = ctk.CTkFrame(self, fg_color="transparent", height=30)
        self.status_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=(0, 5), sticky="ew")
        self.status_label = ctk.CTkLabel(self.status_frame, text="", anchor="w", text_color=self.THEME["color"]["text_secondary"], font=self.THEME["font"]["main"])
        self.status_label.pack(side="left", padx=5, pady=1)

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
        self.results_frame = ctk.CTkScrollableFrame(self.main_frame, label_text=self.tr("combinations"),
                                            fg_color="transparent",
                                            label_font=self.THEME["font"]["subtitle"],
                                            label_text_color=self.THEME["color"]["text_primary"])
        self.results_frame.grid(row=7, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")
        self.results_frame.grid_columnconfigure(0, weight=1)
        self.results_frame.grid_columnconfigure(1, weight=1)
        self.main_frame.grid_rowconfigure(7, weight=1) # Allow results frame to expand

        # --- Pagination Controls ---
        self.pagination_frame = ctk.CTkFrame(self.main_frame)
        self.pagination_frame.grid(row=8, column=0, columnspan=2, pady=(2, 0), sticky="ew")
        self.pagination_frame.grid_columnconfigure((0, 2), weight=1) # Center the label
        self.pagination_frame.grid_remove() # Hide initially

        self.prev_button = ctk.CTkButton(self.pagination_frame, text=self.tr("previous"), command=self.previous_page, state="disabled")
        self.prev_button.grid(row=0, column=0, sticky="e", padx=10)

        self.page_label = ctk.CTkLabel(self.pagination_frame, text=self.tr("page_template", current=1, total=1))
        self.page_label.grid(row=0, column=1, padx=10)

        self.next_button = ctk.CTkButton(self.pagination_frame, text=self.tr("next"), command=self.next_page, state="disabled")
        self.next_button.grid(row=0, column=2, sticky="w", padx=10)

        # --- Loading Animation ---
        self.loading_frame = ctk.CTkFrame(self.main_frame)
        self.loading_label = ctk.CTkLabel(self.loading_frame, text=self.tr("generating_combinations"), font=("Arial", 18))
        self.loading_label.pack(pady=10, padx=10)
        self.loading_animation_label = ctk.CTkLabel(self.loading_frame, text="", font=("Courier", 20))
        self.loading_animation_label.pack(pady=5)
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
        self.change_language(get_language_label(self.current_language))

    def change_language(self, language: str):
        current_category = get_canonical_category(self.category_menu.get()) if hasattr(self, "category_menu") else "All"
        current_preset_key = self.preset_display_to_key.get(self.presets_menu.get(), self.default_preset_key) if hasattr(self, "presets_menu") else self.default_preset_key
        self.current_language = get_language_code(language)

        self.title(self.tr("window_title"))
        self.title_label.configure(text=self.tr("app_title"))
        self.label_interface.configure(text=self.tr("select_interface"))
        self.label_category.configure(text=self.tr("select_module_type"))
        self.label_presets.configure(text=self.tr("select_preset"))
        self.save_preset_button.configure(text=self.tr("save"))
        self.delete_preset_button.configure(text=self.tr("delete"))
        self.start_button.configure(text=self.tr("start_monitoring"))
        self.stop_button.configure(text=self.tr("stop_monitoring"))
        self.rescreen_button.configure(text=self.tr("start_optimization"))
        self.import_csv_button.configure(text=self.tr("import_csv"))
        self.export_csv_button.configure(text=self.tr("export_csv"))
        self.priority_order_checkbox.configure(text=self.tr("enable_priority_ordering"))
        self.label_dist_filter.configure(text=self.tr("attr_distribution"))
        self.results_frame.configure(label_text=self.tr("combinations"))
        self.prev_button.configure(text=self.tr("previous"))
        self.next_button.configure(text=self.tr("next"))
        self.loading_label.configure(text=self.tr("generating_combinations"))
        self.category_menu.configure(values=get_category_options(self.current_language))
        self.category_menu.set(get_category_label(current_category, self.current_language))
        self.attribute_buttons["All"].configure(text=self.tr("all"))

        if self.monitor_instance:
            self.monitor_instance.language = self.current_language
            self.monitor_instance.module_optimizer.language = self.current_language

        for attr in self.all_attributes:
            self.attribute_buttons[attr].configure(text=self.get_display_attribute_name(attr))

        if self.current_status_key:
            self.update_status_label(self.tr(self.current_status_key), self.current_status_key)
        else:
            self.update_status_label(self.current_status_message)
        self.update_dist_filter_buttons()
        self.update_presets_menu(current_preset_key)
        self.update_priority_attrs_ui()
        self.update_dynamic_instruction()

        if self.base_instruction_key:
            self.base_instruction_text = self.tr(self.base_instruction_key)
            if self.instruction_label_simple.winfo_viewable():
                self.instruction_label_simple.configure(text=self.base_instruction_text)

        if self.solutions_cache:
            self.display_current_page()
        else:
            self.page_label.configure(text=self.tr("page_template", current=1, total=1))


    def update_filter_warning_text(self):
        # Esta función ya no es necesaria para mostrar advertencias dinámicas.
        return "" # Siempre devuelve una cadena vacía

    def update_filter_status(self):
        # Esta función ya no tiene ninguna acción ya que el warning frame fue eliminado.
        pass

    def update_dynamic_instruction(self):
        # Clear previous widgets
        for widget in self.instruction_text_frame.winfo_children():
            widget.destroy()

        ctk.CTkLabel(self.instruction_text_frame, text=self.tr("dynamic_instruction_1"), font=self.THEME["font"]["small"]).pack(side="left")
        ctk.CTkLabel(
            self.instruction_text_frame,
            text=self.tr("dynamic_instruction_button"),
            font=("Segoe UI", 12, "bold"),
            fg_color="#1F6AA5",
            corner_radius=5
        ).pack(side="left", padx=2)
        ctk.CTkLabel(self.instruction_text_frame, text=self.tr("dynamic_instruction_2"), font=self.THEME["font"]["small"]).pack(side="left")

    def get_resource_path(self, *parts: str) -> str:
        return str(self.resource_base_dir.joinpath(*parts))

    def _apply_window_icon(self) -> None:
        icon_path = Path(self.get_resource_path("icon.ico"))
        if not icon_path.exists():
            logging.warning(f"ウィンドウアイコンが見つかりません: {icon_path}")
            return

        try:
            self.iconbitmap(str(icon_path))
        except tkinter.TclError as exc:
            logging.warning(f"ウィンドウアイコンを設定できませんでした: {exc}")

    def ensure_presets_file(self) -> None:
        if self.presets_file_path.exists():
            return

        source_path = Path(self.get_resource_path("custom_presets.json"))
        default_presets = {self.default_preset_key: ""}

        try:
            if source_path.exists():
                self.presets_file_path.write_text(
                    source_path.read_text(encoding="utf-8"),
                    encoding="utf-8",
                )
                return
        except OSError as exc:
            logging.warning(f"既定プリセットのコピーに失敗しました: {exc}")

        self.presets_file_path.write_text(
            json.dumps(default_presets, indent=4, ensure_ascii=False),
            encoding="utf-8",
        )

    def run_file_dialog(self, callback):
        self.attributes("-topmost", False)
        try:
            return callback()
        finally:
            self.attributes("-topmost", True)

    def clear_results_display(self):
        self.all_solutions_cache = []
        self.solutions_cache = []
        self.current_page = 0
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        self.pagination_frame.grid_remove()
        self.dist_filter_frame.grid_remove()
        self.results_frame.grid_remove()

    def tr(self, key: str, **kwargs) -> str:
        text = self.translations[self.current_language].get(key, self.translations["en"].get(key, key))
        return text.format(**kwargs) if kwargs else text

    def get_display_attribute_name(self, attribute_name: str) -> str:
        return get_attribute_label(attribute_name, self.current_language)

    def get_display_preset_name(self, preset_name: str) -> str:
        return get_preset_display_name(preset_name, self.current_language)

    def has_captured_module_data(self) -> bool:
        return bool(self.monitor_instance and self.monitor_instance.has_captured_data())

    def is_monitoring_active(self) -> bool:
        return bool(self.monitor_instance and self.monitor_instance.is_running)

    def get_current_optimization_settings(self):
        category = get_canonical_category(self.category_menu.get())
        attributes = list(self.selected_attributes)
        prioritized_attrs = self.ordered_prioritized_attrs if self.priority_order_checkbox.get() == 1 else []
        priority_order_mode = self.priority_order_checkbox.get() == 1
        return category, attributes, prioritized_attrs, priority_order_mode

    def create_monitor_instance(self, interface_name: str = "") -> StarResonanceMonitor:
        category, attributes, prioritized_attrs, priority_order_mode = self.get_current_optimization_settings()
        return StarResonanceMonitor(
            interface_name=interface_name,
            category=category,
            attributes=attributes,
            prioritized_attrs=prioritized_attrs,
            priority_order_mode=priority_order_mode,
            language=self.current_language,
            on_data_captured_callback=self.enable_optimization,
            progress_callback=self.progress_callback,
            on_results_callback=self.results_callback,
        )

    def update_optimization_button_state(self):
        has_data = self.has_captured_module_data()
        is_monitoring = self.is_monitoring_active()
        optimize_state = "normal" if has_data and not is_monitoring else "disabled"
        export_state = "normal" if has_data and not is_monitoring else "disabled"
        import_state = "disabled" if is_monitoring else "normal"

        self.rescreen_button.configure(state=optimize_state)
        self.export_csv_button.configure(state=export_state)
        self.import_csv_button.configure(state=import_state)

    def update_status_label(self, message: str, status_key: Optional[str] = None):
        self.current_status_key = status_key
        self.current_status_message = message
        self.status_label.configure(text=f"{self.tr('status_prefix')}{message}")


    def load_font_awesome(self) -> Optional[CTkFont]:
        """Loads the Font Awesome font if available."""
        font_path = self.get_resource_path("Font Awesome 7 Free-Solid-900.otf")
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
                logging.error(f"Font Awesome フォントを読み込めませんでした: {e}")
                return None
        else:
            logging.warning(f"Font Awesome ファイルが見つかりません: '{font_path}'。アイコン文字は表示されません。")
            return None

    def load_module_images(self) -> Dict[str, ctk.CTkImage]:
        """Loads all module images from the Modulos directory."""
        images = {}
        image_dir = Path(self.get_resource_path("Modulos"))
        if not image_dir.is_dir():
            logging.warning(f"画像ディレクトリ '{image_dir}' が見つかりません。")
            return images
        
        for image_path in image_dir.iterdir():
            if image_path.suffix.lower() == ".webp":
                try:
                    # Match names like "Epic Attack" from "Epic Attack.webp"
                    name = image_path.stem
                    img = Image.open(image_path).resize((60, 60), Image.Resampling.LANCZOS)
                    images[name] = ctk.CTkImage(light_image=img, dark_image=img, size=(60, 60))
                except Exception as e:
                    logging.error(f"画像 {image_path.name} の読み込みに失敗しました: {e}")
        return images

    def load_attribute_images(self) -> Dict[str, ctk.CTkImage]:
        """Loads all attribute icon images from the Module-Effects directory."""
        images = {}
        image_dir = Path(self.get_resource_path("Module-Effects"))
        if not image_dir.is_dir():
            logging.warning(f"画像ディレクトリ '{image_dir}' が見つかりません。")
            return images
        
        for image_path in image_dir.iterdir():
            if image_path.suffix.lower() == ".webp":
                try:
                    # Match names like "Armor" from "Armor.webp"
                    name = image_path.stem
                    img = Image.open(image_path).resize((18, 18), Image.Resampling.LANCZOS)
                    images[name] = ctk.CTkImage(light_image=img, dark_image=img, size=(18, 18))
                except Exception as e:
                    logging.error(f"属性アイコン {image_path.name} の読み込みに失敗しました: {e}")
        return images

    def toggle_filters(self):
        if self.filters_frame.winfo_viewable():
            self.filters_frame.grid_remove()
        else:
            self.filters_frame.grid()

    def toggle_attribute(self, attribute_name: str):
        """Toggles the selection state of an attribute button and manages priority order list."""
        if attribute_name in self.selected_attributes:
            self.selected_attributes.remove(attribute_name)
            self.attribute_buttons[attribute_name].configure(fg_color=self.THEME["color"]["background_secondary"])
            # Remove from ordered list if present
            if attribute_name in self.ordered_prioritized_attrs:
                self.ordered_prioritized_attrs.remove(attribute_name)
        else:
            if len(self.ordered_prioritized_attrs) < 6: # Limit to 6 prioritized attributes
                self.selected_attributes.add(attribute_name)
                self.attribute_buttons[attribute_name].configure(fg_color="#1F6AA5") # Blue
                # Add to ordered list if not already there
                if attribute_name not in self.ordered_prioritized_attrs:
                    self.ordered_prioritized_attrs.append(attribute_name)
            else:
                logging.warning(self.tr("priority_limit_warning"))
                # Optionally, inform the user via a tooltip or status message
        
        # Update "All" button state
        if len(self.selected_attributes) == len(self.all_attributes):
            self.attribute_buttons["All"].configure(fg_color="#1F6AA5")
        else:
            self.attribute_buttons["All"].configure(fg_color=self.THEME["color"]["background_secondary"])
        
        self.update_filter_status() # Update warning status
        self.update_priority_attrs_ui() # Update the UI for ordered attributes

    def toggle_all_attributes(self):
        """Toggles all attributes on or off and manages priority order list."""
        if len(self.selected_attributes) == len(self.all_attributes):
            # If all are selected, deselect all
            self.selected_attributes.clear()
            self.ordered_prioritized_attrs.clear() # Clear ordered list as well
            for attr, button in self.attribute_buttons.items():
                button.configure(fg_color=self.THEME["color"]["background_secondary"])
        else:
            # If not all are selected, select all
            self.selected_attributes.update(self.all_attributes)
            for attr, button in self.attribute_buttons.items():
                if attr != "All":
                    button.configure(fg_color="#1F6AA5")
            self.attribute_buttons["All"].configure(fg_color="#1F6AA5")
            
            # If priority mode is enabled, add up to 6 attributes to the ordered list
            if self.priority_order_checkbox.get() == 1:
                self.ordered_prioritized_attrs = [attr for attr in self.all_attributes if attr in self.selected_attributes][:6]
            else:
                self.ordered_prioritized_attrs.clear() # Ensure it's clear if not in priority mode

        self.update_filter_status() # Update warning status
        self.update_priority_attrs_ui() # Update the UI for ordered attributes

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
                if "ゲームサーバーを識別しました" in record or "识别到游戏服务器" in record:
                    self.instruction_text_frame.pack_forget()
                    if not self.instruction_label_simple.winfo_viewable():
                        self.instruction_label_simple.pack(side="left", padx=(0, 5), pady=2)
                    
                    self.instruction_icon.configure(text="🔄", text_color="#1E90FF") # Blue sync icon
                    self.base_instruction_key = "waiting_for_modules"
                    self.base_instruction_text = self.tr(self.base_instruction_key)
                    self.instruction_label_simple.configure(text=self.base_instruction_text)
                    self.start_instruction_animation()
            except queue.Empty:
                break
        
        # Process progress queue
        while True:
            try:
                message = self.progress_queue.get(block=False)
                self.update_status_label(message)
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
        self.update_optimization_button_state()
        self.apply_filters_and_redisplay()

    def display_current_page(self):
        """Clears and rebuilds the results display for the current page."""
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        if not self.solutions_cache:
            self.pagination_frame.grid_remove()
            no_results_label = ctk.CTkLabel(self.results_frame, text=self.tr("no_valid_combinations"), font=("Segoe UI", 16))
            no_results_label.pack(pady=20)
            return

        total_pages = (len(self.solutions_cache) - 1) // self.results_per_page + 1
        self.page_label.configure(text=self.tr("page_template", current=self.current_page + 1, total=total_pages))

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

            solution_frame = ctk.CTkFrame(self.results_frame, 
                              fg_color=self.THEME["color"]["background_secondary"], 
                              border_color=self.THEME["color"]["border"], # Borde sutil
                              border_width=1, 
                              corner_radius=15)
            solution_frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            solution_frame.grid_columnconfigure(0, weight=1)

            header_frame = ctk.CTkFrame(solution_frame, fg_color="transparent")
            header_frame.grid(row=0, column=0, padx=5, pady=(2, 5), sticky="ew")
            header_frame.grid_columnconfigure(0, weight=1)
            header_frame.grid_columnconfigure(1, weight=1)

            left_header_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
            left_header_frame.grid(row=0, column=0, sticky="w")

            header_label = ctk.CTkLabel(
                left_header_frame, 
                text=self.tr("rank_template", rank=rank, score=solution.optimization_score),
                font=self.THEME["font"]["subtitle"],
                text_color=self.THEME["color"]["text_primary"]
            )
            header_label.pack(side="left")

            right_header_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
            right_header_frame.grid(row=0, column=1, sticky="e")

            total_attr_value = sum(solution.attr_breakdown.values())
            
            # The combat power is stored in the \'score\' attribute of the solution.
            combat_power = getattr(solution, 'score', 'N/A')
            if isinstance(combat_power, (int, float)):
                combat_power = f"{combat_power:.0f}"

            stats_text = f"{self.tr('total_attributes')}: {total_attr_value} | {self.tr('ability_score')}: {combat_power}"
            stats_label = ctk.CTkLabel(
                right_header_frame,
                text=stats_text,
                font=self.THEME["font"]["small"],
                text_color=self.THEME["color"]["text_secondary"]
            )
            stats_label.pack(side="right")

            content_frame = ctk.CTkFrame(solution_frame, fg_color="transparent")
            content_frame.grid(row=1, column=0, padx=5, pady=2, sticky="ew")
            content_frame.grid_columnconfigure(0, weight=1)

            modules_container = ctk.CTkFrame(content_frame, fg_color="transparent")
            modules_container.grid(row=0, column=0, pady=2, sticky="nsew")
            
            for j, module in enumerate(solution.modules):
                modules_container.grid_columnconfigure(j, weight=1)
                rarity = module.name.split()[0]
                # Quita el color de rareza del fondo para un look más limpio, o hazlo más sutil.
                # Por ejemplo, puedes poner el color en el borde.
                rarity_colors = {
                    "Rare": "#34558b",
                    "Epic": "#6f42c1",
                    "Legendary": "#ffc107"
                }
                color = rarity_colors.get(rarity, self.THEME["color"]["border"])
                module_card = ctk.CTkFrame(modules_container,
                                   fg_color=self.THEME["color"]["background_main"], # Fondo neutro
                                   border_width=1,
                                   border_color=color, # Usa el color de rareza en el borde
                                   corner_radius=10,
                                   width=190) # Añadir un ancho fijo para que los textos no se ajusten
                module_card.grid(row=0, column=j, padx=2, pady=2, sticky="ns")

                img_label = ctk.CTkLabel(module_card, image=self.module_images.get(module.name), text="")
                img_label.pack(pady=(2, 2), padx=2)
                
                attrs_frame = ctk.CTkFrame(module_card, fg_color="transparent")
                attrs_frame.pack(pady=2, padx=2, anchor="w", fill="x")

                for part in module.parts:
                    attr_line_frame = ctk.CTkFrame(attrs_frame, fg_color="transparent")
                    attr_line_frame.pack(anchor="w")
                    
                    icon = self.attribute_images.get(part.name)
                    if icon:
                        icon_label = ctk.CTkLabel(attr_line_frame, image=icon, text="")
                        icon_label.pack(side="left", padx=(0, 2))

                    attr_text = f"{self.get_display_attribute_name(part.name)}+{part.value}"
                    attrs_label = ctk.CTkLabel(attr_line_frame, text=attr_text, 
                                           font=self.THEME["font"]["small"],
                                           text_color=self.THEME["color"]["text_primary"])
                    attrs_label.pack(side="left")

            stats_frame = ctk.CTkFrame(content_frame)
            stats_frame.grid(row=1, column=0, pady=5, sticky="nsew")

            ctk.CTkLabel(stats_frame, text=self.tr("attribute_distribution"), font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=5, pady=(2, 1))
            
            attr_dist_frame = ctk.CTkFrame(stats_frame, fg_color="transparent")
            attr_dist_frame.pack(anchor="w", padx=5, pady=1, fill="x")

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

                attr_dist_text = f"{self.get_display_attribute_name(attr_name)} {level_str}: +{value}"
                ctk.CTkLabel(attr_line_frame, text=attr_dist_text, font=("Segoe UI", 11), justify="left").pack(side="left")

    def set_distribution_filter(self, filter_name: str):
        """Sets the distribution filter and re-applies it to the cached results."""
        self.distribution_filter = filter_name
        self.update_dist_filter_buttons()
        logging.info(f"属性分布フィルターを変更しました: {get_distribution_filter_label(filter_name, self.current_language)}")
        self.apply_filters_and_redisplay()

    def update_dist_filter_buttons(self):
        """Updates the appearance of distribution filter buttons."""
        # This color should ideally be from the theme, but this is a simple way
        selected_color = "#1F6AA5" # A blue color from the default theme
        default_color = ctk.ThemeManager.theme["CTkButton"]["fg_color"]
        
        for name, button in self.dist_filter_buttons.items():
            button.configure(text=get_distribution_filter_label(name, self.current_language))
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
        self.ensure_presets_file()
        try:
            with open(self.presets_file_path, "r", encoding="utf-8") as f:
                self.presets = json.load(f)
            if self.default_preset_key not in self.presets:
                self.presets[self.default_preset_key] = ""
        except (FileNotFoundError, json.JSONDecodeError):
            self.presets = {self.default_preset_key: ""} # Default
            self.save_presets_to_file()

    def save_presets_to_file(self):
        self.presets_file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.presets_file_path, "w", encoding="utf-8") as f:
            json.dump(self.presets, f, indent=4, ensure_ascii=False)

    def update_presets_menu(self, selected_preset_key: Optional[str] = None):
        display_values = []
        self.preset_display_to_key = {}
        for preset_name in self.presets.keys():
            display_name = self.get_display_preset_name(preset_name)
            display_values.append(display_name)
            self.preset_display_to_key[display_name] = preset_name
        self.presets_menu.configure(values=display_values)
        target_preset = selected_preset_key if selected_preset_key in self.presets else self.default_preset_key
        self.presets_menu.set(self.get_display_preset_name(target_preset))

    def update_priority_attrs_ui(self):
        """Builds or clears the UI for ordered prioritized attributes based on checkbox state."""
        # Clear existing widgets in the container
        for widget in self.priority_attrs_container.winfo_children():
            widget.destroy()

        if self.priority_order_checkbox.get() == 1:
            self.priority_attrs_container.grid() # Ensure container is visible
            
            if not self.ordered_prioritized_attrs:
                label = ctk.CTkLabel(self.priority_attrs_container, text=self.tr("select_priority_attrs"), 
                                     font=self.THEME["font"]["small"], 
                                     text_color=self.THEME["color"]["text_secondary"])
                label.pack(pady=5)
                return

            for idx, attr_name in enumerate(self.ordered_prioritized_attrs):
                attr_row_frame = ctk.CTkFrame(self.priority_attrs_container, fg_color="transparent")
                attr_row_frame.grid(row=idx, column=0, padx=2, pady=1, sticky="ew")
                attr_row_frame.grid_columnconfigure(0, weight=1) # Attribute name takes most space

                # Attribute Name
                attr_label = ctk.CTkLabel(attr_row_frame, text=f"{idx+1}. {self.get_display_attribute_name(attr_name)}", 
                                          font=self.THEME["font"]["main"], 
                                          text_color=self.THEME["color"]["text_primary"],
                                          anchor="w")
                attr_label.grid(row=0, column=0, sticky="ew", padx=(0, 5))

                # Up button
                up_button = ctk.CTkButton(attr_row_frame, text="▲", width=30, height=24,
                                          fg_color=self.THEME["color"]["background_main"],
                                          text_color=self.THEME["color"]["text_primary"],
                                          hover_color=self.THEME["color"]["border"],
                                          command=lambda a=attr_name: self.move_priority_attr(a, -1))
                up_button.grid(row=0, column=1, padx=(0, 1))
                if idx == 0: up_button.configure(state="disabled")

                # Down button
                down_button = ctk.CTkButton(attr_row_frame, text="▼", width=30, height=24,
                                            fg_color=self.THEME["color"]["background_main"],
                                            text_color=self.THEME["color"]["text_primary"],
                                            hover_color=self.THEME["color"]["border"],
                                            command=lambda a=attr_name: self.move_priority_attr(a, 1))
                down_button.grid(row=0, column=2, padx=(0, 1))
                if idx == len(self.ordered_prioritized_attrs) - 1: down_button.configure(state="disabled")

                # Remove button
                remove_button = ctk.CTkButton(attr_row_frame, text="✕", width=30, height=24,
                                              fg_color="#FF4500", # Red color for remove
                                              text_color=self.THEME["color"]["text_primary"],
                                              hover_color="#DC143C",
                                              command=lambda a=attr_name: self.remove_priority_attr(a))
                remove_button.grid(row=0, column=3)
        else:
            self.priority_attrs_container.grid_remove() # Hide container if checkbox is unchecked
            self.ordered_prioritized_attrs.clear() # Clear ordered list when disabled

    def move_priority_attr(self, attr_name: str, direction: int):
        """Moves an attribute up or down in the ordered prioritized list."""
        if attr_name not in self.ordered_prioritized_attrs:
            return

        current_idx = self.ordered_prioritized_attrs.index(attr_name)
        new_idx = current_idx + direction

        if 0 <= new_idx < len(self.ordered_prioritized_attrs):
            self.ordered_prioritized_attrs[current_idx], self.ordered_prioritized_attrs[new_idx] = \
                self.ordered_prioritized_attrs[new_idx], self.ordered_prioritized_attrs[current_idx]
            self.update_priority_attrs_ui()

    def remove_priority_attr(self, attr_name: str):
        """Removes an attribute from the ordered prioritized list."""
        if attr_name in self.ordered_prioritized_attrs:
            self.ordered_prioritized_attrs.remove(attr_name)
            self.selected_attributes.discard(attr_name) # Also deselect from pill buttons
            if attr_name in self.attribute_buttons:
                self.attribute_buttons[attr_name].configure(fg_color=self.THEME["color"]["background_secondary"])
            self.update_priority_attrs_ui()
            self.update_filter_status() # Update warning status

    def apply_preset(self, preset_name: str):
        preset_name = self.preset_display_to_key.get(preset_name, preset_name)
        attributes_str = self.presets.get(preset_name, "")
        preset_attributes = set()
        if attributes_str:
            # Split the string by commas and then strip whitespace from each attribute
            temp_attributes = [attr.strip() for attr in attributes_str.split(",") if attr.strip()]
            for attr in temp_attributes:
                if attr in self.all_attributes:
                    preset_attributes.add(attr)

        # Clear current selections and ordered list
        for attr in list(self.selected_attributes):
            self.toggle_attribute(attr) # This will remove from selected_attributes and ordered_prioritized_attrs

        # Select attributes from the preset, adding to ordered list in preset's string order
        # Assuming attributes_str preserves a meaningful order if it's used for priority
        if self.priority_order_checkbox.get() == 1 and attributes_str:
            # If priority mode is on, populate ordered_prioritized_attrs directly from preset string order
            self.ordered_prioritized_attrs.clear()
            for attr in temp_attributes: # Use temp_attributes which is already ordered
                if attr in self.all_attributes and attr not in self.ordered_prioritized_attrs and len(self.ordered_prioritized_attrs) < 6:
                    self.ordered_prioritized_attrs.append(attr)
                    self.selected_attributes.add(attr) # Ensure it's marked as selected
                    if attr in self.attribute_buttons:
                        self.attribute_buttons[attr].configure(fg_color="#1F6AA5")
        else:
            # Fallback to normal selection behavior if priority mode is off or no string
            for attr in preset_attributes:
                if attr not in self.selected_attributes: # Only toggle if not already selected
                    self.toggle_attribute(attr)
        
        self.update_filter_status()
        self.update_priority_attrs_ui()

    def save_preset(self):
        title = self.tr("save_preset_title")
        prompt = self.tr("save_preset_prompt")
        
        dialog = ctk.CTkInputDialog(text=prompt, title=title)
        self.attributes("-topmost", False)
        preset_name = dialog.get_input()
        self.attributes("-topmost", True)

        if preset_name and preset_name not in self.presets:
            # Join attributes with a comma and space
            current_attributes = ", ".join(sorted(list(self.selected_attributes)))
            self.presets[preset_name] = current_attributes
            self.save_presets_to_file()
            self.update_presets_menu(preset_name)
            self.presets_menu.set(self.get_display_preset_name(preset_name))

    def delete_preset(self):
        preset_display_name = self.presets_menu.get()
        preset_name = self.preset_display_to_key.get(preset_display_name, preset_display_name)
        if preset_name == self.default_preset_key:
            return # Cannot delete the default
        
        title = self.tr("delete_preset_title")
        prompt = self.tr("delete_preset_prompt", preset_name=self.get_display_preset_name(preset_name))

        if tkinter.messagebox.askyesno(title, prompt):
            if preset_name in self.presets:
                del self.presets[preset_name]
                self.save_presets_to_file()
                self.update_presets_menu()

    def export_modules_csv(self):
        if not self.has_captured_module_data():
            logging.warning(self.tr("no_export_data"))
            return

        file_path = self.run_file_dialog(
            lambda: filedialog.asksaveasfilename(
                title=self.tr("csv_export_title"),
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialdir=str(self.user_data_dir),
                initialfile="modules.csv",
            )
        )
        if not file_path:
            return

        try:
            modules = self.monitor_instance.captured_modules if self.monitor_instance else []
            export_modules_to_csv(modules, file_path)
            message = self.tr("csv_export_success", count=len(modules))
            logging.info(f"{message} ({file_path})")
            self.update_status_label(message)
        except Exception as exc:
            logging.error(self.tr("csv_export_failed", error=exc))

    def import_modules_csv(self):
        if self.is_monitoring_active():
            logging.warning(self.tr("stop_monitoring_before_import"))
            return

        file_path = self.run_file_dialog(
            lambda: filedialog.askopenfilename(
                title=self.tr("csv_import_title"),
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialdir=str(self.user_data_dir),
            )
        )
        if not file_path:
            return

        try:
            modules = import_modules_from_csv(file_path)
            self.clear_results_display()
            self.monitor_instance = self.create_monitor_instance("")
            self.monitor_instance.captured_modules = modules
            self.monitor_thread = None
            message = self.tr("csv_import_success", count=len(modules))
            logging.info(f"{message} ({file_path})")
            self.enable_optimization()
        except Exception as exc:
            logging.error(self.tr("csv_import_failed", error=exc))

    def start_monitoring(self):
        selected_interface_display = self.interface_menu.get()
        if not selected_interface_display:
            logging.error(self.tr("select_interface_first"))
            return
        
        interface_name = self.interface_map[selected_interface_display]

        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        self.log_textbox.insert("end", self.tr("start_notice"))
        self.log_textbox.configure(state="disabled")
        self.update_status_label(self.tr("starting_monitoring"), "starting_monitoring")
        
        # Update instruction label
        self.instruction_text_frame.pack_forget()
        self.instruction_label_simple.pack(side="left", padx=(0, 5), pady=2)
        self.instruction_icon.configure(text="⚠️", text_color="#FFA500") # Orange warning
        self.base_instruction_key = "change_channel_instruction"
        self.base_instruction_text = self.tr(self.base_instruction_key)
        self.instruction_label_simple.configure(text=self.base_instruction_text)
        self.instruction_frame.grid()

        # Clear previous results and cache
        self.clear_results_display()

        self.monitor_instance = self.create_monitor_instance(interface_name)
        
        self.monitor_thread = threading.Thread(target=self.monitor_instance.start_monitoring, daemon=True)
        self.monitor_thread.start()

        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.interface_menu.configure(state="disabled")
        self.category_menu.configure(state="normal")
        self.update_optimization_button_state()
        self.update_status_label(self.tr("monitoring_game_data"), "monitoring_game_data")

    def stop_monitoring(self):
        if self.monitor_instance:
            self.monitor_instance.stop_monitoring()
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=1.0)

        self.monitor_thread = None

        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.interface_menu.configure(state="normal")
        self.category_menu.configure(state="normal") # Category menu should be enabled after stopping
        self.update_optimization_button_state()
        if self.has_captured_module_data():
            self.update_status_label(self.tr("data_captured_ready"), "data_captured_ready")
        else:
            self.update_status_label(self.tr("idle"), "idle")
        self.dist_filter_frame.grid_remove() # Hide distribution filter
        self.stop_instruction_animation()

        # Reset instruction label to the appropriate state
        self.instruction_label_simple.pack_forget()
        if self.has_captured_module_data():
            ready_message = self.tr("data_captured_ready")
            self.base_instruction_key = "data_captured_ready"
            self.base_instruction_text = ready_message
            self.instruction_label_simple.configure(text=ready_message)
            self.instruction_label_simple.pack(side="left", padx=(0, 5), pady=2)
            self.instruction_text_frame.pack_forget()
            self.instruction_icon.configure(text="✓", text_color="#32CD32")
        else:
            self.base_instruction_key = "change_channel_instruction"
            self.base_instruction_text = self.tr(self.base_instruction_key)
            self.update_dynamic_instruction() # Re-create the initial instruction in the correct language
            self.instruction_text_frame.pack(side="left", padx=(0, 10), pady=5)
            self.instruction_icon.configure(text="⚠️", text_color="#FFCC00") # Yellow warning
        self.instruction_frame.grid()

    def start_optimization(self):
        """保持中のモジュール一覧を使って最適化を実行する。"""
        if not self.monitor_instance or not self.monitor_instance.has_captured_data():
            logging.warning(self.tr("no_rescreen_data"))
            return

        # Clear cache and show loading animation
        self.solutions_cache = []
        self.current_page = 0
        self.pagination_frame.grid_remove()
        self.results_frame.grid_remove()
        self.instruction_frame.grid_remove() # Hide instructions
        self.loading_frame.grid(row=8, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        self.start_animation()
        
        category = get_canonical_category(self.category_menu.get())
        attributes = list(self.selected_attributes)
        prioritized_attrs = self.ordered_prioritized_attrs if self.priority_order_checkbox.get() == 1 else []
        priority_order_mode = self.priority_order_checkbox.get() == 1
        
        logging.info(self.tr("rescreen_requested"))
        self.rescreen_button.configure(state="disabled")
        
        threading.Thread(
            target=self.monitor_instance.optimize_modules,
            args=(category, attributes, prioritized_attrs, priority_order_mode),
            daemon=True
        ).start()
    
    def rescreen_results(self):
        """互換性維持用。内部的には最適化開始を実行する。"""
        self.start_optimization()

    def enable_optimization(self):
        """キャプチャ完了通知を UI スレッドへ中継する。"""
        self.after(0, self._on_captured_data_ready)

    def _on_captured_data_ready(self):
        self.stop_instruction_animation()
        self.instruction_text_frame.pack_forget()
        if not self.instruction_label_simple.winfo_viewable():
            self.instruction_label_simple.pack(side="left", padx=(0, 5), pady=2)

        self.update_optimization_button_state()
        if self.is_monitoring_active():
            message = self.tr("captured_data_waiting_stop")
            self.base_instruction_key = "captured_data_waiting_stop"
        else:
            message = self.tr("data_captured_ready")
            self.base_instruction_key = "data_captured_ready"

        self.base_instruction_text = message
        self.instruction_label_simple.configure(text=message)
        self.instruction_icon.configure(text="✓", text_color="#32CD32")
        self.instruction_frame.grid()
        self.update_status_label(message, "captured_data_waiting_stop" if self.is_monitoring_active() else "data_captured_ready")
        
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

# star_resonance_monitor_core.py

import logging
import time
import threading # Import threading
from typing import Dict, List, Any, Optional, Callable

from localization import (
    DEFAULT_LANGUAGE,
    format_attribute_list,
    get_canonical_category,
    get_category_label,
)
from logging_config import get_logger
from module_parser import ModuleParser
from module_optimizer import ModuleOptimizer, ModuleCategory
from packet_capture import PacketCapture

logger = get_logger(__name__)

class StarResonanceMonitor:
    """Star Resonance Monitor"""

    def __init__(self, interface_name: str, category: str = "攻击", attributes: List[str] = None,
                 prioritized_attrs: Optional[List[str]] = None, priority_order_mode: bool = False,
                 language: str = DEFAULT_LANGUAGE,
                 on_data_captured_callback: Optional[Callable] = None,
                 progress_callback: Optional[Callable[[str], None]] = None,
                 on_results_callback: Optional[Callable[[List[Any]], None]] = None): # Add results callback
        self.interface_name = interface_name
        self.initial_category = category
        self.initial_attributes = attributes or []
        self.initial_prioritized_attrs = prioritized_attrs or []
        self.initial_priority_order_mode = priority_order_mode
        self.language = language
        self.on_data_captured_callback = on_data_captured_callback
        self.progress_callback = progress_callback
        self.on_results_callback = on_results_callback # Save results callback
        
        self.is_running = False
        self.captured_modules: Optional[List[Any]] = None

        self.packet_capture = PacketCapture(self.interface_name)
        self.module_parser = ModuleParser()
        self.module_optimizer = ModuleOptimizer(language=self.language)

    def _is_japanese(self) -> bool:
        return self.language == "ja"

    def _format_attributes(self, attributes: List[str]) -> str:
        return format_attribute_list(attributes, self.language)

    def start_monitoring(self):
        self.is_running = True
        display_category = get_category_label(get_canonical_category(self.initial_category), self.language)
        if self._is_japanese():
            print(f"初期モジュール種別: {display_category}\n")
        else:
            print(f"Tipo de Módulo Inicial: {display_category}\n")
        if self.initial_attributes:
            if self._is_japanese():
                print(f"初期属性フィルター: {self._format_attributes(self.initial_attributes)}\n")
            else:
                print(f"Filtro de Atributos Inicial: {', '.join(self.initial_attributes)}\n")
        else:
            print("初期属性フィルター: なし\n" if self._is_japanese() else "Filtro de Atributos Inicial: Ninguno\n")
        print(f"ネットワークインターフェース名: {self.interface_name}\n" if self._is_japanese() else f"Nombre de la Interfaz de Red: {self.interface_name}\n")

        self.packet_capture.start_capture(self._on_sync_container_data)
        if self._is_japanese():
            print("監視を開始しました。チャンネル変更、再ログイン、またはキャラクター切替を行ってモジュール情報を送信してください。\n")
        else:
            print("Monitoreo iniciado, por favor cambia de línea, vuelve a iniciar sesión o cambia de personaje para obtener información del módulo...\n")

    def stop_monitoring(self):
        if not self.is_running:
            return
        self.is_running = False
        self.packet_capture.stop_capture()
        print("=== 監視を停止しました ===" if self._is_japanese() else "=== Monitoring Stopped ===")

    def _on_sync_container_data(self, data: Dict[str, Any]):
        try:
            v_data = data.get('v_data')
            if v_data:
                print("モジュールデータを取得しました。解析を開始します。" if self._is_japanese() else "Module data captured, starting parsing...")
                all_modules = self.module_parser.parse_module_info(v_data)
                
                if all_modules:
                    # Only store data and trigger callback on first capture
                    if self.captured_modules is None:
                        self.captured_modules = all_modules
                        if self._is_japanese():
                            print(f"{len(self.captured_modules)} 件のモジュールを解析して保存しました。")
                            print("監視停止後に最適化を実行できます。")
                        else:
                            print(f"Successfully parsed and stored {len(self.captured_modules)} modules.")
                            print("You can stop monitoring and run optimization afterwards.")
                        
                        # Notify GUI to enable "Rescreen" button
                        if self.on_data_captured_callback:
                            self.on_data_captured_callback()
                    else:
                        if self._is_japanese():
                            print("モジュールデータは既に取得済みのため、後続パケットは無視します。更新するには監視をやり直してください。")
                        else:
                            print("Module data already captured, ignoring subsequent packets. Restart monitoring to update.")
                else:
                    print("パケット内に有効なモジュール情報が見つかりませんでした。" if self._is_japanese() else "No valid module information found in packet.")
        except Exception as e:
            logger.error(f"データパケットの処理に失敗しました: {e}" if self._is_japanese() else f"Failed to process data packet: {e}")

    def has_captured_data(self) -> bool:
        """Checks if module data has been captured and stored"""
        return self.captured_modules is not None

    def _run_optimization_in_background(self, category: str, attributes: List[str], 
                                         prioritized_attrs: List[str], priority_order_mode: bool):
        """
        Runs the optimization process in a separate thread to avoid blocking the UI.
        """
        if not self.has_captured_data():
            logger.error("最適化に使用できるモジュールデータがありません。" if self._is_japanese() else "Error: No module data available for optimization.")
            return

        print("\n--- 新しい条件でバックグラウンド最適化を開始します ---" if self._is_japanese() else "\n--- Starting optimization in background with new conditions ---")
        if self._is_japanese():
            print(f"モジュール種別: {get_category_label(get_canonical_category(category), self.language)}")
            print(f"属性フィルター: {self._format_attributes(attributes) if attributes else 'なし'}")
        else:
            print(f"Module Type: {category}")
            print(f"Filtered Attributes: {', '.join(attributes) if attributes else 'None'}")
        if priority_order_mode and prioritized_attrs:
            if self._is_japanese():
                print(f"優先属性順: {self._format_attributes(prioritized_attrs)}")
            else:
                print(f"Prioritized Ordering (top 4): {', '.join(prioritized_attrs)}")
        
        canonical_category = get_canonical_category(category)
        category_map = {
            "All": ModuleCategory.All,
            "Attack": ModuleCategory.ATTACK,
            "Guard": ModuleCategory.GUARDIAN,
            "Support": ModuleCategory.SUPPORT,
        }
        target_category = category_map.get(canonical_category, ModuleCategory.All)
        
        if self._is_japanese():
            logger.info(f"対象カテゴリ: {target_category} (入力値: '{category}')")
        else:
            logger.info(f"Target Category: {target_category} (from input '{category}')")
        
        try:
            solutions = self.module_optimizer.get_optimal_solutions(
                self.captured_modules,
                target_category,
                top_n=20,
                prioritized_attrs=prioritized_attrs if priority_order_mode else attributes, # Pass prioritized_attrs for ordering
                priority_order_mode=priority_order_mode,
                progress_callback=self.progress_callback
            )

            if self.on_results_callback:
                self.on_results_callback(solutions)
            
            num_solutions = len(solutions)
            for i, solution in enumerate(reversed(solutions)):
                rank = num_solutions - i
                self.module_optimizer.print_solution_details(solution, rank)
        except Exception as e:
            logger.error(f"最適化処理に失敗しました: {e}" if self._is_japanese() else f"Optimization process failed: {e}")
            if self.progress_callback:
                self.progress_callback("最適化に失敗しました。" if self._is_japanese() else "Optimization failed.")

    def rescreen_modules(self, category: str, attributes: List[str], 
                         prioritized_attrs: Optional[List[str]] = None, priority_order_mode: bool = False):
        """Rescreens captured data with new filter conditions by running optimization in a separate thread."""
        if not self.has_captured_data():
            print("再フィルターできるモジュールデータがありません。" if self._is_japanese() else "Error: No module data available for rescreening.")
            return

        # Start the optimization in a new thread
        optimization_thread = threading.Thread(
            target=self._run_optimization_in_background,
            args=(category, attributes, prioritized_attrs, priority_order_mode),
            daemon=True
        )
        optimization_thread.start()

    def optimize_modules(self, category: str, attributes: List[str],
                         prioritized_attrs: Optional[List[str]] = None, priority_order_mode: bool = False):
        """保持中のモジュール一覧に対して最適化を実行する。"""
        self.rescreen_modules(category, attributes, prioritized_attrs, priority_order_mode)

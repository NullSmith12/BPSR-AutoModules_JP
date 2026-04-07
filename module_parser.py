# module_parser.py

import json
import logging
from typing import Dict, List, Optional, Any
from BlueProtobuf_pb2 import CharSerialize
from logging_config import get_logger
from module_types import (
    ModuleInfo, ModulePart, MODULE_NAMES, MODULE_ATTR_NAMES
)

logger = get_logger(__name__)

def is_iterable(obj):
    """辅助函数：检查一个对象是否是可迭代的（但不是字符串）。"""
    if isinstance(obj, str):
        return False
    try:
        iter(obj)
        return True
    except TypeError:
        return False

class ModuleParser:
    """模组解析器"""
    
    def __init__(self):
        self.logger = logger
    
    def parse_module_info(self, v_data: CharSerialize, attributes: List[str] = None, 
                         exclude_attributes: List[str] = None, match_count: int = 1) -> List[ModuleInfo]:
        """
        仅解析模组信息并根据基础规则进行过滤，不再调用优化器。
        返回解析后的模组列表。
        """
        self.logger.info("モジュール解析を開始します...")
        mod_infos = v_data.Mod.ModInfos
        modules = []

        for package_type, package in v_data.ItemPackage.Packages.items():
            if not (item := next(iter(package.Items.values()), None)) or not item.HasField('ModNewAttr'):
                continue # 如果不是模组背包，则跳过

            for key, item in package.Items.items():
                if item.HasField('ModNewAttr') and item.ModNewAttr.ModParts:
                    config_id = item.ConfigId
                    mod_info_details = mod_infos.get(key)
                    if not mod_info_details: continue

                    module_info = ModuleInfo(
                        name=MODULE_NAMES.get(config_id, f"不明なモジュール({config_id})"),
                        config_id=config_id,
                        uuid=item.Uuid,
                        quality=item.Quality,
                        parts=[]
                    )

                    # --- 错误修正开始 ---
                    # 原始数据可能是一个整数（当只有一个部件时），也可能是一个列表。
                    # 我们需要统一处理成列表格式。
                    raw_mod_parts = item.ModNewAttr.ModParts
                    mod_parts = [raw_mod_parts] if not is_iterable(raw_mod_parts) else list(raw_mod_parts)
                    
                    raw_init_link_nums = mod_info_details.InitLinkNums
                    init_link_nums = [raw_init_link_nums] if not is_iterable(raw_init_link_nums) else list(raw_init_link_nums)
                    # --- 错误修正结束 ---

                    for i, part_id in enumerate(mod_parts):
                        if i < len(init_link_nums):
                            module_info.parts.append(ModulePart(
                                id=part_id,
                                name=MODULE_ATTR_NAMES.get(part_id, f"不明な属性({part_id})"),
                                value=init_link_nums[i]
                            ))
                    modules.append(module_info)
        
        self.logger.info(f"{len(modules)} 件のモジュールを解析しました。")
        
        if attributes or exclude_attributes:
            filtered_modules = self._filter_modules_by_attributes(modules, attributes, exclude_attributes, match_count)
            self.logger.info(f"基本属性ルールで絞り込んだ後の残件数: {len(filtered_modules)}")
            return filtered_modules
        else:
            return modules
    
    def _filter_modules_by_attributes(self, modules: List[ModuleInfo], attributes: List[str] = None, 
                                     exclude_attributes: List[str] = None, match_count: int = 1) -> List[ModuleInfo]:
        """根据属性词条筛选模组 (私有辅助方法)"""
        if not attributes and not exclude_attributes:
            return modules

        filtered_modules = []
        for module in modules:
            module_attrs = {part.name for part in module.parts}
            
            if exclude_attributes and any(attr in module_attrs for attr in exclude_attributes):
                continue
            
            if attributes:
                matching_attrs_count = sum(1 for attr in attributes if attr in module_attrs)
                if matching_attrs_count >= match_count:
                    filtered_modules.append(module)
            else:
                filtered_modules.append(module)
        
        return filtered_modules

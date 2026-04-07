"""
モジュール一覧の CSV 入出力。
"""

import csv
import re
from pathlib import Path
from typing import Dict, List, Optional

from localization import get_attribute_label, get_module_name_label
from module_types import MODULE_ATTR_IDS, MODULE_ATTR_NAMES, MODULE_CATEGORY_MAP, MODULE_NAMES, ModuleInfo, ModulePart


MODULE_NAME_IDS: Dict[str, int] = {name: config_id for config_id, name in MODULE_NAMES.items()}
JA_MODULE_NAME_IDS: Dict[str, int] = {
    get_module_name_label(name, "ja"): config_id
    for name, config_id in MODULE_NAME_IDS.items()
}
JA_ATTRIBUTE_NAME_IDS: Dict[str, int] = {
    get_attribute_label(name, "ja"): attr_id
    for name, attr_id in MODULE_ATTR_IDS.items()
}

PART_COLUMN_PATTERN = re.compile(r"part(\d+)_(id|name|name_ja|value)$")


def export_modules_to_csv(modules: List[ModuleInfo], path: str) -> None:
    """モジュール一覧を CSV へ書き出す。"""
    csv_path = Path(path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    max_parts = max((len(module.parts) for module in modules), default=0)
    fieldnames = [
        "name",
        "name_ja",
        "config_id",
        "category",
        "uuid",
        "quality",
        "part_count",
    ]

    for index in range(1, max_parts + 1):
        fieldnames.extend([
            f"part{index}_id",
            f"part{index}_name",
            f"part{index}_name_ja",
            f"part{index}_value",
        ])

    with csv_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()

        for module in sorted(modules, key=lambda item: item.uuid):
            category = MODULE_CATEGORY_MAP.get(module.config_id)
            row = {
                "name": module.name,
                "name_ja": get_module_name_label(module.name, "ja"),
                "config_id": module.config_id,
                "category": category.value if category else "",
                "uuid": module.uuid,
                "quality": module.quality,
                "part_count": len(module.parts),
            }

            for index, part in enumerate(module.parts, start=1):
                row[f"part{index}_id"] = part.id
                row[f"part{index}_name"] = part.name
                row[f"part{index}_name_ja"] = get_attribute_label(part.name, "ja")
                row[f"part{index}_value"] = part.value

            writer.writerow(row)


def import_modules_from_csv(path: str) -> List[ModuleInfo]:
    """CSV からモジュール一覧を読み込む。"""
    csv_path = Path(path)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV ファイルが見つかりません: {csv_path}")

    with csv_path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError("CSV ヘッダーが見つかりません。")

        part_indexes = _get_part_indexes(reader.fieldnames)
        if not part_indexes:
            raise ValueError("CSV に属性列が見つかりません。")

        modules: List[ModuleInfo] = []
        used_uuids = set()
        next_generated_uuid = -1

        for row_number, row in enumerate(reader, start=2):
            if _is_empty_row(row):
                continue

            config_id = _parse_int(row.get("config_id"), "config_id", row_number, default=None)
            module_name = _resolve_module_name(
                raw_name=(row.get("name") or "").strip(),
                raw_name_ja=(row.get("name_ja") or "").strip(),
                config_id=config_id,
                row_number=row_number,
            )
            if config_id is None:
                config_id = MODULE_NAME_IDS.get(module_name)
                if config_id is None:
                    raise ValueError(f"{row_number} 行目: モジュール種別を特定できません。")

            raw_uuid = _parse_int(row.get("uuid"), "uuid", row_number, default=None)
            module_uuid = raw_uuid
            if module_uuid is None or module_uuid in used_uuids:
                while next_generated_uuid in used_uuids:
                    next_generated_uuid -= 1
                module_uuid = next_generated_uuid
                next_generated_uuid -= 1
            used_uuids.add(module_uuid)

            quality = _parse_int(row.get("quality"), "quality", row_number, default=0) or 0
            parts = _parse_parts(row, row_number, part_indexes)
            if not parts:
                raise ValueError(f"{row_number} 行目: 属性情報がありません。")

            modules.append(
                ModuleInfo(
                    name=module_name,
                    config_id=config_id,
                    uuid=module_uuid,
                    quality=quality,
                    parts=parts,
                )
            )

    if not modules:
        raise ValueError("CSV からモジュールを読み込めませんでした。")

    return modules


def _get_part_indexes(fieldnames: List[str]) -> List[int]:
    indexes = set()
    for fieldname in fieldnames:
        match = PART_COLUMN_PATTERN.match(fieldname or "")
        if match:
            indexes.add(int(match.group(1)))
    return sorted(indexes)


def _is_empty_row(row: Dict[str, Optional[str]]) -> bool:
    return all(not (value or "").strip() for value in row.values())


def _parse_int(raw_value: Optional[str], field_name: str, row_number: int, default: Optional[int] = None) -> Optional[int]:
    value = (raw_value or "").strip()
    if value == "":
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{row_number} 行目: {field_name} の値 '{value}' は整数ではありません。") from exc


def _resolve_module_name(raw_name: str, raw_name_ja: str, config_id: Optional[int], row_number: int) -> str:
    if config_id is not None and config_id in MODULE_NAMES:
        return MODULE_NAMES[config_id]

    if raw_name in MODULE_NAME_IDS:
        return raw_name

    if raw_name_ja in JA_MODULE_NAME_IDS:
        config_id = JA_MODULE_NAME_IDS[raw_name_ja]
        return MODULE_NAMES.get(config_id, raw_name_ja)

    if raw_name:
        return raw_name

    raise ValueError(f"{row_number} 行目: モジュール名または config_id が必要です。")


def _resolve_part_id(raw_id: Optional[int], raw_name: str, raw_name_ja: str, row_number: int, part_index: int) -> int:
    if raw_id is not None:
        return raw_id

    if raw_name in MODULE_ATTR_IDS:
        return MODULE_ATTR_IDS[raw_name]

    if raw_name_ja in JA_ATTRIBUTE_NAME_IDS:
        return JA_ATTRIBUTE_NAME_IDS[raw_name_ja]

    raise ValueError(f"{row_number} 行目: part{part_index} の属性 ID または属性名を解決できません。")


def _parse_parts(row: Dict[str, Optional[str]], row_number: int, part_indexes: List[int]) -> List[ModulePart]:
    parts: List[ModulePart] = []

    for part_index in part_indexes:
        raw_id_text = (row.get(f"part{part_index}_id") or "").strip()
        raw_name = (row.get(f"part{part_index}_name") or "").strip()
        raw_name_ja = (row.get(f"part{part_index}_name_ja") or "").strip()
        raw_value_text = (row.get(f"part{part_index}_value") or "").strip()

        if not any([raw_id_text, raw_name, raw_name_ja, raw_value_text]):
            continue

        value = _parse_int(raw_value_text, f"part{part_index}_value", row_number)
        if value is None:
            raise ValueError(f"{row_number} 行目: part{part_index}_value が空です。")

        raw_id = _parse_int(raw_id_text, f"part{part_index}_id", row_number, default=None)
        part_id = _resolve_part_id(raw_id, raw_name, raw_name_ja, row_number, part_index)
        part_name = MODULE_ATTR_NAMES.get(part_id, raw_name or raw_name_ja or f"不明な属性({part_id})")

        parts.append(ModulePart(id=part_id, name=part_name, value=value))

    return parts

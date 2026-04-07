"""
表示用のローカライズ補助。
内部キーは既存の英語名を維持し、表示時のみ locales 配下の辞書へ変換する。
"""

from pathlib import Path
import json
from typing import Any, Dict, List


BASE_DIR = Path(__file__).resolve().parent
LOCALES_DIR = BASE_DIR / "locales"

FALLBACK_MANIFEST: Dict[str, Any] = {
    "default": "ja",
    "languages": {
        "ja": "日本語",
        "en": "English",
        "es": "Español",
    },
}

CATEGORY_ORDER: List[str] = ["All", "Attack", "Guard", "Support"]
CATEGORY_TEXT_KEYS: Dict[str, str] = {
    "All": "category_all",
    "Attack": "category_attack",
    "Guard": "category_guard",
    "Support": "category_support",
}

DISTRIBUTION_FILTER_ORDER: List[str] = ["All", "Lv.5", "Lv.5/Lv.5", "Lv.5/Lv.6", "Lv.6/Lv.6"]
DISTRIBUTION_FILTER_TEXT_KEYS: Dict[str, str] = {
    "All": "dist_all",
    "Lv.5": "dist_lv5",
    "Lv.5/Lv.5": "dist_lv5_lv5",
    "Lv.5/Lv.6": "dist_lv5_lv6",
    "Lv.6/Lv.6": "dist_lv6_lv6",
}

APP_TEXT_KEY_MAP: Dict[str, str] = {
    "select_interface": "select_interface",
    "select_module_type": "select_module_type",
    "select_preset": "select_preset",
    "dynamic_instruction_1": "dynamic_instruction_1",
    "dynamic_instruction_button": "dynamic_instruction_button",
    "dynamic_instruction_2": "dynamic_instruction_2",
    "waiting_for_modules": "waiting_for_modules",
    "change_channel_instruction": "change_channel_instruction",
    "refilter": "refilter",
    "save_preset_title": "save_preset_title",
    "save_preset_prompt": "save_preset_prompt",
    "delete_preset_title": "delete_preset_title",
    "delete_preset_prompt": "delete_preset_prompt",
    "save": "save",
    "delete": "delete",
    "enable_priority_ordering": "enable_priority_ordering",
    "select_priority_attrs": "select_priority_attrs",
    "start_monitoring": "start_monitoring",
    "stop_monitoring": "stop_monitoring",
    "attr_distribution": "distribution_filter",
    "combinations": "results_title",
    "previous": "previous_page",
    "next": "next_page",
    "page_template": "page_label",
    "generating_combinations": "loading_text",
    "no_valid_combinations": "no_results",
    "rank_template": "rank_text",
    "total_attributes": "total_attributes",
    "ability_score": "ability_score",
    "attribute_distribution": "attribute_distribution",
    "status_prefix": "status_prefix",
    "idle": "status_idle",
    "starting_monitoring": "status_starting",
    "monitoring_game_data": "status_monitoring",
    "data_captured_ready": "status_data_captured",
    "start_notice": "start_log_message",
    "all": "all_button",
}

MANUAL_PRESET_KEYS = {"Manual Input / Clear", "__manual_input_clear__"}

MODULE_NAME_LABELS: Dict[str, Dict[str, str]] = {
    "Rare Attack": {"ja": "レア攻撃", "en": "Rare Attack", "es": "Ataque raro"},
    "Epic Attack": {"ja": "エピック攻撃", "en": "Epic Attack", "es": "Ataque épico"},
    "Legendary Attack": {"ja": "レジェンダリー攻撃", "en": "Legendary Attack", "es": "Ataque legendario"},
    "Legendary Attack-Preferred": {"ja": "優先レジェンダリー攻撃", "en": "Legendary Attack-Preferred", "es": "Ataque legendario prioritario"},
    "Rare Support": {"ja": "レア支援", "en": "Rare Support", "es": "Soporte raro"},
    "Epic Support": {"ja": "エピック支援", "en": "Epic Support", "es": "Soporte épico"},
    "Legendary Support": {"ja": "レジェンダリー支援", "en": "Legendary Support", "es": "Soporte legendario"},
    "Legendary Support-Preferred": {"ja": "優先レジェンダリー支援", "en": "Legendary Support-Preferred", "es": "Soporte legendario prioritario"},
    "Rare Guard": {"ja": "レア防御", "en": "Rare Guard", "es": "Guardia rara"},
    "Epic Guard": {"ja": "エピック防御", "en": "Epic Guard", "es": "Guardia épica"},
    "Legendary Guard": {"ja": "レジェンダリー防御", "en": "Legendary Guard", "es": "Guardia legendaria"},
    "Legendary Guard-Preferred": {"ja": "優先レジェンダリー防御", "en": "Legendary Guard-Preferred", "es": "Guardia legendaria prioritaria"},
}

RARITY_LABELS: Dict[str, Dict[str, str]] = {
    "Rare": {"ja": "レア", "en": "Rare", "es": "Raro"},
    "Epic": {"ja": "エピック", "en": "Epic", "es": "Épico"},
    "Legendary": {"ja": "レジェンダリー", "en": "Legendary", "es": "Legendario"},
}


def _load_json(path: Path, fallback: Dict[str, Any]) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return fallback.copy()


MANIFEST = _load_json(LOCALES_DIR / "manifest.json", FALLBACK_MANIFEST)
DEFAULT_LANGUAGE = MANIFEST.get("default", "ja")
LANGUAGE_LABELS: Dict[str, str] = dict(MANIFEST.get("languages", FALLBACK_MANIFEST["languages"]))
LANGUAGE_ORDER: List[str] = list(LANGUAGE_LABELS.keys())
LANGUAGE_CODES_BY_LABEL: Dict[str, str] = {
    label: code for code, label in LANGUAGE_LABELS.items()
}
LOCALE_DATA: Dict[str, Dict[str, Any]] = {
    language: _load_json(LOCALES_DIR / f"{language}.json", {})
    for language in LANGUAGE_ORDER
}


def normalize_language(language: str) -> str:
    """サポート対象外の言語コードは既定値へ寄せる。"""
    return language if language in LANGUAGE_LABELS else DEFAULT_LANGUAGE


def get_locale_data(language: str) -> Dict[str, Any]:
    language = normalize_language(language)
    return LOCALE_DATA.get(language, LOCALE_DATA.get(DEFAULT_LANGUAGE, {}))


def get_locale_text(text_key: str, language: str, default: str = "") -> str:
    language = normalize_language(language)
    locale_data = get_locale_data(language)
    if text_key in locale_data:
        return locale_data[text_key]

    if language != "en":
        en_data = LOCALE_DATA.get("en", {})
        if text_key in en_data:
            return en_data[text_key]

    return default or text_key


def get_app_translations() -> Dict[str, Dict[str, str]]:
    translations: Dict[str, Dict[str, str]] = {}
    for language in LANGUAGE_ORDER:
        translations[language] = {
            app_key: get_locale_text(locale_key, language)
            for app_key, locale_key in APP_TEXT_KEY_MAP.items()
        }
    return translations


def get_language_options() -> List[str]:
    return [LANGUAGE_LABELS[code] for code in LANGUAGE_ORDER]


def get_language_code(label: str) -> str:
    return LANGUAGE_CODES_BY_LABEL.get(label, DEFAULT_LANGUAGE)


def get_language_label(code: str) -> str:
    return LANGUAGE_LABELS.get(normalize_language(code), LANGUAGE_LABELS[DEFAULT_LANGUAGE])


def get_category_label(category: str, language: str) -> str:
    return get_locale_text(CATEGORY_TEXT_KEYS.get(category, ""), language, category)


def get_category_options(language: str) -> List[str]:
    return [get_category_label(category, language) for category in CATEGORY_ORDER]


def get_canonical_category(label: str) -> str:
    for category in CATEGORY_ORDER:
        if label == category:
            return category
        for language in LANGUAGE_ORDER:
            if label == get_category_label(category, language):
                return category
    return "All"


def get_distribution_filter_label(filter_name: str, language: str) -> str:
    return get_locale_text(DISTRIBUTION_FILTER_TEXT_KEYS.get(filter_name, ""), language, filter_name)


def get_attribute_label(name: str, language: str) -> str:
    locale_data = get_locale_data(language)
    ability_names = locale_data.get("ability_names", {})
    if name in ability_names:
        return ability_names[name]

    if language != "en":
        en_names = LOCALE_DATA.get("en", {}).get("ability_names", {})
        if name in en_names:
            return en_names[name]

    return name


def get_attribute_labels(names: List[str], language: str) -> List[str]:
    return [get_attribute_label(name, language) for name in names]


def format_attribute_list(names: List[str], language: str) -> str:
    return ", ".join(get_attribute_labels(names, language))


def get_module_name_label(name: str, language: str) -> str:
    language = normalize_language(language)
    return MODULE_NAME_LABELS.get(name, {}).get(language, name)


def get_rarity_label(name: str, language: str) -> str:
    language = normalize_language(language)
    return RARITY_LABELS.get(name, {}).get(language, name)


def get_preset_display_name(name: str, language: str) -> str:
    locale_data = get_locale_data(language)
    preset_names = locale_data.get("preset_names", {})

    if name in MANUAL_PRESET_KEYS:
        return preset_names.get("__manual_input_clear__", get_locale_text("preset_manual_clear", language, name))

    if name in preset_names:
        return preset_names[name]

    if language != "en":
        en_preset_names = LOCALE_DATA.get("en", {}).get("preset_names", {})
        if name in en_preset_names:
            return en_preset_names[name]

    return name

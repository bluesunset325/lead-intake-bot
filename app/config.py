import os
import yaml
from pathlib import Path
from typing import Optional, Dict, Any
from functools import lru_cache

CONFIG_DIR = Path(__file__).parent.parent / "configs" / "clients"


def load_client_config(client_key: str) -> Dict[str, Any]:
    # <key>.yaml, а если его нет — default.yaml
    if client_key and client_key != "default":
        config_file = CONFIG_DIR / f"{client_key}.yaml"
    else:
        config_file = CONFIG_DIR / "default.yaml"
    
    if not config_file.exists():
        config_file = CONFIG_DIR / "default.yaml"
    
    with open(config_file, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@lru_cache(maxsize=32)
def get_client_config_cached(client_key: str) -> Dict[str, Any]:
    return load_client_config(client_key)


def get_welcome_text(config: Dict[str, Any]) -> str:
    return config.get("welcome_text", "Добро пожаловать!")


def get_thank_you_text(config: Dict[str, Any]) -> str:
    return config.get("thank_you_text", "Спасибо! Мы свяжемся с вами.")


def get_questions(config: Dict[str, Any]) -> list:
    return config.get("questions", [])


def get_budget_choices(config: Dict[str, Any]) -> list:
    return config.get("budget_choices", ["<10k", "10-30k", "30-70k", "70k+"])


def get_urgency_choices(config: Dict[str, Any]) -> list:
    return config.get("urgency_choices", ["Сегодня", "На этой неделе", "В этом месяце"])

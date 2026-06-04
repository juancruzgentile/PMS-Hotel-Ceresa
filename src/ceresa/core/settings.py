"""
Application settings for Ceresa.

Ceresa uses two layers of configuration:

1. MODULE_DEFINITIONS:
   Describes all modules known by the system.

2. config/modules.json:
   Defines which modules are enabled for this hotel installation.

This allows Ceresa to adapt to different hotels without changing Python code.
"""

import json
from pathlib import Path


APP_NAME = "Ceresa PMS"
APP_VERSION = "0.1.0"


BASE_DIR = Path(__file__).resolve().parents[3]
CONFIG_DIR = BASE_DIR / "config"
MODULES_CONFIG_PATH = CONFIG_DIR / "modules.json"


MODULE_DEFINITIONS = {
    "rooms": {
        "description": "Room management module.",
    },
    "housekeeping": {
        "description": "Housekeeping and cleaning workflow module.",
    },
    "maintenance": {
        "description": "Maintenance workflow module.",
    },
    "kitchen": {
        "description": "Kitchen and meal planning module. Future module.",
    },
    "sala": {
        "description": "Dining room and waiter service module. Future module.",
    },
    "laundry": {
        "description": "Laundry stock and workflow module. Future module.",
    },
    "inventory": {
        "description": "Inventory and stock control module. Future module.",
    },
    "accounting": {
        "description": "Income, expenses and accounting module. Future module.",
    },
    "clients": {
        "description": "Guest/client application module. Future module.",
    },
    "transport": {
        "description": "Guest transport, driver assignment and GPS coordination module. Future module.",
    },
    "locks": {
        "description": "Digital locks and key card integration module. Future module.",
    },
    "lights": {
        "description": "Smart lights control module. Future module.",
    },
    "air_conditioning": {
        "description": "Air conditioning control module. Future module.",
    },
    "broken_module": {
        "description": "Intentional broken module used to test module isolation.",
    },
}


DEFAULT_MODULES_CONFIG = {
    "rooms": True,
    "housekeeping": True,
    "maintenance": True,
    "kitchen": False,
    "sala": False,
    "laundry": False,
    "inventory": False,
    "accounting": False,
    "clients": False,
    "transport": False,
    "locks": False,
    "lights": False,
    "air_conditioning": False,
    "broken_module": False,
}


def load_modules_config() -> dict[str, bool]:
    """
    Loads module activation settings from config/modules.json.

    If the file does not exist or is invalid, Ceresa falls back to
    DEFAULT_MODULES_CONFIG so the system can still start safely.
    """
    if not MODULES_CONFIG_PATH.exists():
        return DEFAULT_MODULES_CONFIG.copy()

    try:
        raw_data = json.loads(MODULES_CONFIG_PATH.read_text(encoding="utf-8"))

        modules_config = DEFAULT_MODULES_CONFIG.copy()

        for module_name, enabled in raw_data.items():
            if module_name in MODULE_DEFINITIONS:
                modules_config[module_name] = bool(enabled)

        return modules_config

    except Exception:
        return DEFAULT_MODULES_CONFIG.copy()


def get_modules() -> dict:
    """
    Builds the final MODULES dictionary used by the module loader.

    Each module receives:
    - enabled: from config/modules.json
    - description: from MODULE_DEFINITIONS
    """
    modules_config = load_modules_config()
    modules = {}

    for module_name, definition in MODULE_DEFINITIONS.items():
        modules[module_name] = {
            "enabled": modules_config.get(module_name, False),
            "description": definition["description"],
        }

    return modules


MODULES = get_modules()
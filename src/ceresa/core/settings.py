"""
Application settings for Ceresa.

Ceresa uses configuration files to adapt the system to different hotels.

Configuration files:
- config/modules.json: enables or disables modules.
- config/hotel.json: stores basic hotel installation settings.
"""

import json
from pathlib import Path


APP_NAME = "Ceresa PMS"
APP_VERSION = "0.1.0"


BASE_DIR = Path(__file__).resolve().parents[3]
CONFIG_DIR = BASE_DIR / "config"

MODULES_CONFIG_PATH = CONFIG_DIR / "modules.json"
HOTEL_CONFIG_PATH = CONFIG_DIR / "hotel.json"


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
    "users": {
        "description": "Users, departments and staff hierarchy module.",
},
    "reception": {
        "description": "Reception, check-in, check-out and guest coordination module.",
},
    "kitchen": {
        "description": "Kitchen, meals, allergies and food preparation module.",
},
    "bar": {
        "description": "Bar, drinks, coffee service and beverage stock module.",
},
    "beach": {
        "description": "Beach services, umbrellas, sunbeds and guest beach reservations module.",
},

    "broken_module": {
        "description": "Intentional broken module used to test module isolation.",
    },
}


DEFAULT_MODULES_CONFIG = {
    "rooms": True,
    "housekeeping": True,
    "maintenance": True,
    "sala": False,
    "laundry": False,
    "inventory": False,
    "accounting": False,
    "clients": False,
    "transport": False,
    "locks": False,
    "lights": False,
    "air_conditioning": False,
    "users": True,
    "broken_module": False,
    "reception": True,
    "kitchen": True,
    "bar": True,
    "beach": True,
}


DEFAULT_HOTEL_CONFIG = {
    "hotel_name": "Ceresa Demo Hotel",
    "hotel_category": "not_configured",
    "country": "not_configured",
    "city": "not_configured",
    "timezone": "UTC",
    "currency": "EUR",
    "default_language": "es",
    "floors": 1,
    "has_restaurant": False,
    "has_transport": False,
    "has_pool": False,
    "has_spa": False,
    "has_digital_locks": False,
    "has_smart_lights": False,
    "has_smart_air_conditioning": False,
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
    """
    modules_config = load_modules_config()
    modules = {}

    for module_name, definition in MODULE_DEFINITIONS.items():
        modules[module_name] = {
            "enabled": modules_config.get(module_name, False),
            "description": definition["description"],
        }

    return modules


def load_hotel_config() -> dict:
    """
    Loads basic hotel configuration from config/hotel.json.

    If the file does not exist or is invalid, Ceresa falls back
    to DEFAULT_HOTEL_CONFIG so the app can still start safely.
    """
    if not HOTEL_CONFIG_PATH.exists():
        return DEFAULT_HOTEL_CONFIG.copy()

    try:
        raw_data = json.loads(HOTEL_CONFIG_PATH.read_text(encoding="utf-8"))

        hotel_config = DEFAULT_HOTEL_CONFIG.copy()

        for key, value in raw_data.items():
            if key in DEFAULT_HOTEL_CONFIG:
                hotel_config[key] = value

        return hotel_config

    except Exception:
        return DEFAULT_HOTEL_CONFIG.copy()


MODULES = get_modules()
HOTEL_CONFIG = load_hotel_config()
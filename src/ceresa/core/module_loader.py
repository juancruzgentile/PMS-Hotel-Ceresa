from importlib import import_module
from typing import Any

from fastapi import FastAPI, APIRouter

from ceresa.core.settings import MODULES


AVAILABLE_ROUTERS: dict[str, str] = {
    "rooms": "ceresa.rooms.routes:router",
    "housekeeping": "ceresa.housekeeping.routes:router",
    "maintenance": "ceresa.maintenance.routes:router",
    "users": "ceresa.users.routes:router",
    "broken_module": "ceresa.broken_module.routes:router",
}


LOADED_MODULES: set[str] = set()
FAILED_MODULES: dict[str, str] = {}


def is_module_enabled(module_name: str) -> bool:
    """
    Returns True if a module is enabled in settings.
    """
    module_config = MODULES.get(module_name)

    if module_config is None:
        return False

    return bool(module_config.get("enabled", False))


def import_router(import_path: str) -> APIRouter:
    """
    Imports a router using a string path.

    Example:
    ceresa.rooms.routes:router
    """
    module_path, router_name = import_path.split(":")

    module = import_module(module_path)
    router = getattr(module, router_name)

    if not isinstance(router, APIRouter):
        raise TypeError(f"{import_path} is not a valid APIRouter.")

    return router


def get_modules_status() -> list[dict[str, Any]]:
    """
    Returns all known modules and their current status.
    """
    modules_status = []

    for module_name, config in MODULES.items():
        modules_status.append(
            {
                "name": module_name,
                "enabled": bool(config["enabled"]),
                "implemented": module_name in AVAILABLE_ROUTERS,
                "loaded": module_name in LOADED_MODULES,
                "error": FAILED_MODULES.get(module_name),
                "description": config["description"],
            }
        )

    return modules_status


def load_enabled_modules(app: FastAPI) -> list[str]:
    """
    Loads only enabled and implemented module routers into the FastAPI app.

    If one module fails, Ceresa does not crash.
    The failed module is reported in FAILED_MODULES.
    Other modules keep working.
    """
    loaded_modules = []

    LOADED_MODULES.clear()
    FAILED_MODULES.clear()

    for module_name, import_path in AVAILABLE_ROUTERS.items():
        if not is_module_enabled(module_name):
            continue

        try:
            router = import_router(import_path)
            app.include_router(router)

            LOADED_MODULES.add(module_name)
            loaded_modules.append(module_name)

        except Exception as error:
            FAILED_MODULES[module_name] = str(error)

    return loaded_modules
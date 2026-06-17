import ast
from pathlib import Path

from ceresa.core import settings


SETTINGS_PATH = Path("src/ceresa/core/settings.py")
CRITICAL_MODULE_DICTIONARIES = {
    "MODULE_DEFINITIONS",
    "DEFAULT_MODULES_CONFIG",
}


def _get_assigned_dictionary(
    tree: ast.Module,
    dictionary_name: str,
) -> ast.Dict:
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue

        if not isinstance(node.value, ast.Dict):
            continue

        for target in node.targets:
            if (
                isinstance(target, ast.Name)
                and target.id == dictionary_name
            ):
                return node.value

    raise AssertionError(f"{dictionary_name} was not found.")


def _get_duplicate_string_keys(dictionary_node: ast.Dict) -> list[str]:
    seen_keys: set[str] = set()
    duplicate_keys: list[str] = []

    for key_node in dictionary_node.keys:
        if not isinstance(key_node, ast.Constant):
            continue

        if not isinstance(key_node.value, str):
            continue

        if key_node.value in seen_keys:
            duplicate_keys.append(key_node.value)
            continue

        seen_keys.add(key_node.value)

    return duplicate_keys


def test_critical_settings_dictionaries_do_not_have_duplicate_keys():
    tree = ast.parse(SETTINGS_PATH.read_text(encoding="utf-8"))

    for dictionary_name in CRITICAL_MODULE_DICTIONARIES:
        dictionary_node = _get_assigned_dictionary(
            tree,
            dictionary_name,
        )
        duplicate_keys = _get_duplicate_string_keys(dictionary_node)

        assert duplicate_keys == [], (
            f"{dictionary_name} has duplicated module keys: "
            f"{duplicate_keys}"
        )


def test_module_definitions_and_default_config_have_same_keys():
    assert set(settings.MODULE_DEFINITIONS) == set(
        settings.DEFAULT_MODULES_CONFIG
    )


def test_default_active_modules_preserve_current_effective_state():
    expected_active_modules = {
        "rooms",
        "guests",
        "reservations",
        "reception",
        "billing",
        "housekeeping",
        "maintenance",
        "users",
        "kitchen",
        "bar",
        "dining_room",
        "beach",
        "transport",
        "tourism",
        "security",
        "laundry",
        "leisure",
        "inventory",
        "accounting",
    }
    active_modules = {
        module_name
        for module_name, enabled in settings.DEFAULT_MODULES_CONFIG.items()
        if enabled
    }

    assert active_modules == expected_active_modules


def test_dining_room_remains_configured_and_enabled_by_default():
    assert "dining_room" in settings.MODULE_DEFINITIONS
    assert settings.DEFAULT_MODULES_CONFIG["dining_room"] is True
    assert settings.MODULES["dining_room"]["enabled"] is True


def test_effective_modules_keep_default_config_keys():
    assert set(settings.MODULES) == set(
        settings.DEFAULT_MODULES_CONFIG
    )

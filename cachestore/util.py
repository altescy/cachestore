from __future__ import annotations

import importlib
import pkgutil
import string
import sys


def b62encode(data: bytes) -> str:
    num = int.from_bytes(data, "big")
    characters = string.digits + string.ascii_letters

    encoded = ""
    base: int = len(characters)

    if num < 0:
        return ""

    while num >= base:
        mod = num % base
        num //= base
        encoded = characters[mod] + encoded

    if num > 0:
        encoded = characters[num] + encoded

    return encoded


def import_submodules(package_name: str) -> None:
    importlib.invalidate_caches()

    sys.path.append(".")

    # Import at top level
    module = importlib.import_module(package_name)
    path = getattr(module, "__path__", [])
    path_string = "" if not path else path[0]

    for module_finder, name, _ in pkgutil.walk_packages(path):
        if path_string and getattr(module_finder, "path") != path_string:  # noqa: B009
            continue
        subpackage = f"{package_name}.{name}"
        import_submodules(subpackage)


def import_modules(module_names: list[str]) -> None:
    for module_name in module_names:
        import_submodules(module_name)

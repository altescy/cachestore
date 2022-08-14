from __future__ import annotations

import importlib
import inspect
import pkgutil
import string
import sys
from types import ModuleType
from typing import Any


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
    module = safe_import_module(package_name)
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


def safe_import_module(modulename: str) -> ModuleType:
    for name, module in list(sys.modules.items()):
        try:
            if name == modulename or (
                hasattr(module, "__file__") and modulename == inspect.getmodulename(inspect.getabsfile(module))
            ):
                return module
        except AttributeError:
            pass
    return importlib.import_module(modulename)


def safe_import_object(path: str) -> Any:
    if "." not in path and ":" not in path:
        raise ValueError("Cache name must be formatted as path.to.module:name.")
    if ":" in path:
        modulename, objname = path.rsplit(":", 1)
    else:
        modulename, objname = path.rsplit(".", 1)
    module = safe_import_module(modulename)
    return getattr(module, objname)


def find_variable_path(obj: Any) -> str | None:
    for modulename, module in list(sys.modules.items()):
        if hasattr(module, "__file__"):
            modulename = inspect.getmodulename(inspect.getabsfile(module)) or modulename
        try:
            for varname, value in module.__dict__.items():
                if value is obj:
                    return f"{modulename}:{varname}"
        except AttributeError:
            pass
    return None

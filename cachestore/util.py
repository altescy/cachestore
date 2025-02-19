from __future__ import annotations

import asyncio
import bz2
import gzip
import importlib
import inspect
import lzma
import pkgutil
import string
import sys
import threading
from collections.abc import AsyncIterator
from contextlib import suppress
from queue import Queue
from types import ModuleType
from typing import Any, Callable, Iterator, TypeVar, Union

T = TypeVar("T")


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
        with suppress(AttributeError):
            if name == modulename or (
                hasattr(module, "__file__") and modulename == inspect.getmodulename(inspect.getabsfile(module))
            ):
                return module
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
        if hasattr(module, "__file__") and module.__file__:
            modulename = inspect.getmodulename(inspect.getabsfile(module)) or modulename
        with suppress(AttributeError):
            for varname, value in module.__dict__.items():
                if value is obj:
                    return f"{modulename}:{varname}"
    return None


def detect_open_fn(file: Any) -> Callable:
    if isinstance(file, gzip.GzipFile):
        return gzip.open
    if isinstance(file, bz2.BZ2File):
        return bz2.open
    if isinstance(file, lzma.LZMAFile):
        return lzma.open
    return open


def async_to_sync_iterator(async_iter: AsyncIterator[T]) -> Iterator[T]:
    class _End: ...

    queue = Queue[Union[T, _End]]()
    stop_event = threading.Event()

    async def producer() -> None:
        try:
            async for item in async_iter:
                queue.put(item)
            queue.put(_End())
        finally:
            stop_event.set()

    def run_event_loop() -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(producer())

    thread = threading.Thread(target=run_event_loop, daemon=True)
    thread.start()

    while True:
        item = queue.get_nowait() if not queue.empty() else queue.get()
        if isinstance(item, _End):
            break
        yield item

    stop_event.wait()

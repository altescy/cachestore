from __future__ import annotations

from importlib.metadata import version
from typing import Callable, TypeVar

from cachestore.cache import Cache
from cachestore.formatters import Formatter, PickleFormatter  # noqa: F401
from cachestore.hashers import Hasher, PickleHasher  # noqa: F401
from cachestore.storages import LocalStorage, Storage  # noqa: F401

__version__ = version("cachestore")
__all__ = [
    "__version__",
    "Cache",
    "Formatter",
    "PickleFormatter",
    "Hasher",
    "PickleHasher",
    "Storage",
    "LocalStorage",
    "cache",
]

T = TypeVar("T")


def cache(
    storage: Storage | None = None,
    formatter: Formatter | None = None,
    hasher: Hasher | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    return Cache(storage, formatter, hasher)()

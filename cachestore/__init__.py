from __future__ import annotations

from importlib.metadata import version

from cachestore.cache import Cache  # noqa: F401
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
]

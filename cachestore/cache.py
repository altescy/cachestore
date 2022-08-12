from __future__ import annotations

from functools import wraps
from logging import getLogger
from typing import Any, Callable, TypeVar, cast

from cachestore.formatters import Formatter, PickleFormatter
from cachestore.hashers import Hasher, PickleHasher
from cachestore.metadata import ExecutionInfo, FunctionInfo
from cachestore.storages import LocalStorage, Storage

DEFAULT_CACHE_DIR = ".cache"

logger = getLogger(__name__)

T = TypeVar("T")


class Cache:
    def __init__(
        self,
        storage: Storage | None = None,
        formatter: Formatter | None = None,
        hasher: Hasher | None = None,
    ) -> None:
        self.storage = storage or LocalStorage(DEFAULT_CACHE_DIR)
        self.formatter = formatter or PickleFormatter()
        self.hasher = hasher or PickleHasher()
        self._function_registry: dict[str, FunctionInfo] = {}

    def __call__(self) -> Callable[[Callable[..., T]], Callable[..., T]]:
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            funcinfo = FunctionInfo.build(func)
            self._function_registry[funcinfo.hash(self.hasher)] = funcinfo

            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> T:
                execinfo = ExecutionInfo.build(func, *args, **kwargs)
                key = ".".join((funcinfo.hash(self.hasher), execinfo.hash(self.hasher)))

                if self.storage.exists(key):
                    logger.info("Cache exists: %s", funcinfo.name)
                    with self.storage.open(key, self.formatter.READ_MODE) as file:
                        artifact = cast(T, self.formatter.read(file))
                else:
                    logger.info("Cache does not exists: %s", funcinfo.name)
                    artifact = func(*args, **kwargs)

                    logger.info("Store new artifact: %s", funcinfo.name)
                    with self.storage.open(key, self.formatter.WRITE_MODE) as file:
                        self.formatter.write(file, artifact)

                return artifact

            return wrapper

        return decorator

    def exists(self, func: Callable[..., Any] | FunctionInfo) -> bool:
        if not isinstance(func, FunctionInfo):
            func = FunctionInfo.build(func)
        prefix = func.hash(self.hasher)
        for key in self.storage.all():
            if key.startswith(prefix):
                return True
        return False

    def remove(self, func: Callable[..., Any] | FunctionInfo) -> None:
        if not isinstance(func, FunctionInfo):
            func = FunctionInfo.build(func)
        prefix = func.hash(self.hasher)
        for key in self.storage.all():
            if key.startswith(prefix):
                self.storage.remove(key)

    def funcinfos(self) -> list[FunctionInfo]:
        return list(self._function_registry.values())

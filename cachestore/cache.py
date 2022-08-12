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
        default_storage: Storage | None = None,
        default_formatter: Formatter | None = None,
        default_hasher: Hasher | None = None,
    ) -> None:
        self._default_storage = default_storage or LocalStorage(DEFAULT_CACHE_DIR)
        self._default_formatter = default_formatter or PickleFormatter()
        self._default_hasher = default_hasher or PickleHasher()

    def __call__(
        self,
        storage: Storage | None = None,
        formatter: Formatter | None = None,
        hasher: Hasher | None = None,
    ) -> Callable[[Callable[..., T]], Callable[..., T]]:
        storage = storage or self._default_storage
        formatter = formatter or self._default_formatter
        hasher = hasher or self._default_hasher

        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> T:
                assert storage is not None
                assert formatter is not None
                assert hasher is not None

                funcinfo = FunctionInfo.build(func)
                execinfo = ExecutionInfo.build(func, *args, **kwargs)
                artifact_location = storage.get_artifact_location(funcinfo.hash(hasher), execinfo.hash(hasher))

                if storage.exists(artifact_location):
                    logger.info("Cache exists: %s", funcinfo.name)
                    with storage.open(artifact_location, formatter.READ_MODE) as file:
                        artifact = cast(T, formatter.read(file))
                else:
                    logger.info("Cache does not exists: %s", funcinfo.name)
                    artifact = func(*args, **kwargs)

                    logger.info("Store new artifact: %s", funcinfo.name)
                    with storage.open(artifact_location, formatter.WRITE_MODE) as file:
                        formatter.write(file, artifact)

                return artifact

            return wrapper

        return decorator

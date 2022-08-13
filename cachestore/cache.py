from __future__ import annotations

import datetime
import inspect
from functools import wraps
from logging import getLogger
from typing import Any, Callable, TypeVar, cast

from cachestore.formatters import Formatter, PickleFormatter
from cachestore.hashers import Hasher, PickleHasher
from cachestore.metadata import CacheInfo, ExecutionInfo, FunctionInfo
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

    def __call__(
        self,
        expire: int | datetime.timedelta | datetime.date | datetime.datetime | None = None,
    ) -> Callable[[Callable[..., T]], Callable[..., T]]:
        expired_at: datetime.datetime | None = None
        if isinstance(expire, int):
            expired_at = datetime.datetime.now() + datetime.timedelta(days=expire)
        elif isinstance(expire, datetime.timedelta):
            expired_at = datetime.datetime.now() + expire
        elif isinstance(expire, datetime.datetime):
            expired_at = expire
        elif isinstance(expire, datetime.date):
            expired_at = datetime.datetime(year=expire.year, month=expire.month, day=expire.day)

        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            funcinfo = FunctionInfo.build(func)
            self._function_registry[funcinfo.hash(self.hasher)] = funcinfo

            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> T:
                execinfo = ExecutionInfo.build(func, *args, **kwargs)
                key = ".".join((funcinfo.hash(self.hasher), execinfo.hash(self.hasher)))
                metakey = f"{key}-metadata"

                if self.storage.exists(metakey):
                    with self.storage.open(key, "r") as file:
                        cacheinfo = CacheInfo.from_json(file.read())
                    if cacheinfo.expired_at is not None and cacheinfo.expired_at >= datetime.datetime.now():
                        logger.info("Cache was expired: %s", funcinfo.name)
                        self.storage.remove(key)
                        self.storage.remove(metakey)

                cacheinfo = CacheInfo(
                    function=funcinfo,
                    parameters=execinfo.params,
                    expired_at=expired_at,
                    executed_at=datetime.datetime.now(),
                )
                with self.storage.open(key, "r") as file:
                    file.write(cacheinfo.to_json())

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

            setattr(wrapper, "__signature__", inspect.signature(func))
            setattr(wrapper, "__annotations__", func.__annotations__)

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

from __future__ import annotations

import datetime
import inspect
import json
from functools import wraps
from logging import getLogger
from typing import Any, Callable, Iterator, TypeVar, cast

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

    def _get_key(self, funcinfo: FunctionInfo, execinfo: ExecutionInfo) -> str:
        return ".".join((funcinfo.hash(self.hasher), execinfo.hash(self.hasher)))

    def _get_metakey(self, key: str) -> str:
        return f"metadata-{key}"

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
                key = self._get_key(funcinfo, execinfo)
                metakey = self._get_metakey(key)

                if self.storage.exists(metakey):
                    with self.storage.open(metakey, "r") as file:
                        cacheinfo = CacheInfo.from_dict(json.load(file))
                    if cacheinfo.expired_at is not None and cacheinfo.expired_at <= datetime.datetime.now():
                        logger.info("[%s] Cache was expired, so remove existing artifact.", funcinfo.name)
                        self.storage.remove(key)
                        self.storage.remove(metakey)

                if self.storage.exists(key) and (expired_at is None or expired_at > datetime.datetime.now()):
                    logger.info("[%s] Cache exists", funcinfo.name)
                    with self.storage.open(key, self.formatter.READ_MODE) as file:
                        artifact = cast(T, self.formatter.read(file))
                else:
                    logger.info("[%s] Cache does not exists.", funcinfo.name)
                    artifact = func(*args, **kwargs)

                    logger.info("[%s] Store new artifact.", funcinfo.name)
                    with self.storage.open(key, self.formatter.WRITE_MODE) as file:
                        self.formatter.write(file, artifact)

                    logger.info("[%s] Export metadata.", funcinfo.name)
                    cacheinfo = CacheInfo(
                        function=funcinfo,
                        parameters=execinfo.params,
                        expired_at=expired_at,
                        executed_at=datetime.datetime.now(),
                    )
                    with self.storage.open(metakey, "w") as file:
                        json.dump(cacheinfo.to_dict(), file)

                return artifact

            setattr(wrapper, "__signature__", inspect.signature(func))
            setattr(wrapper, "__annotations__", func.__annotations__)
            setattr(wrapper, "__cachesore_funcinfo", funcinfo)

            return wrapper

        return decorator

    def exists(self, func: Callable[..., Any] | FunctionInfo) -> bool:
        current = datetime.datetime.now()
        exists = False
        for cacheinfo in self.info(func):
            exists |= cacheinfo.expired_at is None or cacheinfo.expired_at > current
        return exists

    def remove(self, func: Callable[..., Any] | FunctionInfo) -> None:
        if not isinstance(func, FunctionInfo):
            func = FunctionInfo.build(func)
        prefix = func.hash(self.hasher)
        for key in self.storage.filter(prefix=prefix):
            self.storage.remove(key)

    def funcinfos(self) -> list[FunctionInfo]:
        return list(self._function_registry.values())

    def info(self, func: Callable[..., Any] | FunctionInfo) -> Iterator[CacheInfo]:
        if not isinstance(func, FunctionInfo):
            func = FunctionInfo.build(func)
        prefix = func.hash(self.hasher)
        for key in self.storage.filter(prefix=prefix):
            metakey = self._get_metakey(key)
            with self.storage.open(metakey, "r") as file:
                yield CacheInfo.from_dict(json.load(file))

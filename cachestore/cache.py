from __future__ import annotations

import datetime
import inspect
import json
import sys
from functools import wraps
from logging import getLogger
from typing import Any, Callable, Iterator, TypeVar, cast

from cachestore.config import CacheSettings, Config
from cachestore.formatters import Formatter
from cachestore.hashers import Hasher
from cachestore.metadata import CacheInfo, ExecutionInfo, FunctionInfo
from cachestore.storages import Storage

logger = getLogger(__name__)

T = TypeVar("T")


class Cache:
    _cache_registry: list["Cache"] = []

    def __init__(
        self,
        name: str | None = None,
        *,
        storage: Storage | None = None,
        formatter: Formatter | None = None,
        hasher: Hasher | None = None,
        disable: bool | None = None,
        config: Config | None = None,
    ) -> None:
        self.config = config or Config()

        self._name = name
        self._storage = storage
        self._formatter = formatter
        self._hasher = hasher
        self._disable = disable

        self._settings: CacheSettings | None = None
        self._function_registry: dict[str, FunctionInfo] = {}

        self._cache_registry.append(self)

    @classmethod
    def by_name(self, name: str) -> Cache | None:
        for cache in self._cache_registry:
            if cache.name == name:
                return cache
        return None

    @property
    def name(self) -> str:
        if self._name is None:
            for name, module in list(sys.modules.items()):
                try:
                    for varname, obj in module.__dict__.items():
                        if obj is self:
                            modulename = inspect.getmodulename(inspect.getabsfile(module))
                            self._name = f"{modulename}:{varname}"
                            break
                except AttributeError:
                    pass
                if self._name is not None:
                    break
            if self._name is None:
                raise RuntimeError("Cannot get cache name.")
        return self._name

    @property
    def settings(self) -> CacheSettings:
        if self._settings is None:
            self._settings = self.config.settings(self.name)
            if self._storage is not None:
                self._settings.storage = self._storage
            if self._formatter is not None:
                self._settings.formatter = self._formatter
            if self._hasher is not None:
                self._settings.hasher = self._hasher
            if self._disable is not None:
                self._settings.disable = self._disable
        return self._settings

    @property
    def storage(self) -> Storage:
        return self.settings.storage

    @property
    def formatter(self) -> Formatter:
        return self.settings.formatter

    @property
    def hasher(self) -> Hasher:
        return self.settings.hasher

    @property
    def disable(self) -> bool:
        return self.settings.disable

    def _get_key(self, funcinfo: FunctionInfo, execinfo: ExecutionInfo) -> str:
        return ".".join((funcinfo.hash(self.hasher), execinfo.hash(self.hasher)))

    def _get_metakey(self, key: str) -> str:
        return f"metadata-{key}"

    def _is_metakey(self, key: str) -> bool:
        return key.startswith("metadata-")

    def __call__(
        self,
        *,
        ignore: set[str] | None = None,
        expire: int | datetime.timedelta | datetime.date | datetime.datetime | None = None,
        disable: bool | None = None,
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

        if disable is None:
            disable = self.disable

        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            funcinfo = FunctionInfo.build(func)
            self._function_registry[funcinfo.hash(self.hasher)] = funcinfo

            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> T:
                if disable:
                    logger.info("[%s] Disable cache.", funcinfo.name)
                    return func(*args, **kwargs)

                execinfo = ExecutionInfo.build(func, *args, **kwargs)
                if ignore:
                    for paramname in ignore:
                        del execinfo.params[paramname]
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

    def prune(self) -> None:
        for key in self.storage.all():
            if not any(
                key.startswith(funchash) or key.startswith(self._get_metakey(funchash))
                for funchash in self._function_registry
            ):
                logger.info("remove %s", key)
                self.storage.remove(key)

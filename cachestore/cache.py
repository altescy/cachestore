from __future__ import annotations

import asyncio
import datetime
import inspect
import json
import types
from functools import wraps
from logging import getLogger
from typing import Any, Callable, Iterable, Iterator, TypeVar, cast

from cachestore.config import CacheSettings, Config
from cachestore.formatters import Formatter
from cachestore.hashers import Hasher
from cachestore.metadata import CacheInfo, ExecutionInfo, FunctionInfo
from cachestore.storages import Storage
from cachestore.util import async_to_sync_iterator, find_variable_path

logger = getLogger(__name__)

T = TypeVar("T")
F = TypeVar("F", bound=Callable)


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
            self._name = find_variable_path(self)
        if self._name is None:
            raise RuntimeError("Cannot get cache name.")
        return self._name

    @property
    def settings(self) -> CacheSettings:
        if self._settings is None:
            self._settings = self.config.cache_settings(self.name)
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
        formatter: Formatter | None = None,
        disable: bool | None = None,
    ) -> Callable[[F], F]:
        def decorator(func: F) -> F:
            funcinfo = FunctionInfo.build(func)
            self._function_registry[funcinfo.hash(self.hasher)] = funcinfo

            function_settings = self.config.function_settings(f"{self.name} {funcinfo.name}")
            if ignore is not None:
                function_settings.ignore = ignore
            if expire is not None:
                function_settings.expire = expire
            if disable is not None:
                function_settings.disable = disable
            if formatter is not None:
                function_settings.formatter = formatter

            empty = object()

            def _cache_exists(key: str) -> bool:
                expired_at = function_settings.expired_at
                executed_at = datetime.datetime.now()
                return self.storage.exists(key) and (expired_at is None or expired_at > executed_at)

            def _save_cache(
                key: str,
                metakey: str,
                execinfo: ExecutionInfo,
                executed_at: datetime.datetime,
                artifact: Any,
            ) -> None:
                expired_at = function_settings.expired_at
                formatter = function_settings.formatter or self.formatter

                logger.info("[%s] Store new artifact.", funcinfo.name)
                with self.storage.open(key, formatter.WRITE_MODE) as file:
                    formatter.write(file, artifact)

                logger.info("[%s] Export metadata.", funcinfo.name)
                cacheinfo = CacheInfo(
                    function=funcinfo,
                    parameters=execinfo.params,
                    expired_at=expired_at,
                    executed_at=executed_at,
                )
                with self.storage.open(metakey, "wt") as file:
                    json.dump(cacheinfo.to_dict(), file)

            def _load_cache(key: str) -> Any:
                formatter = function_settings.formatter or self.formatter
                with self.storage.open(key, formatter.READ_MODE) as file:
                    artifact = formatter.read(file)
                return artifact

            async def _coro_wrapper(
                key: str,
                metakey: str,
                execinfo: ExecutionInfo,
                executed_at: datetime.datetime,
                value: Any = empty,
            ) -> Any:
                if value is empty:
                    value = _load_cache(key)
                else:
                    value = await value
                    _save_cache(key, metakey, execinfo, executed_at, value)
                return value

            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                executed_at = datetime.datetime.now()
                disable = self.disable if function_settings.disable is None else function_settings.disable

                storage = self.storage

                if disable:
                    logger.info("[%s] Disable cache.", funcinfo.name)
                    return func(*args, **kwargs)

                execinfo = ExecutionInfo.build(func, *args, **kwargs)
                for paramname in function_settings.ignore:
                    del execinfo.params[paramname]

                key = self._get_key(funcinfo, execinfo)
                metakey = self._get_metakey(key)

                if storage.exists(metakey):
                    with storage.open(metakey, "rt") as file:
                        cacheinfo = CacheInfo.from_dict(json.load(file))
                    if cacheinfo.expired_at is not None and cacheinfo.expired_at <= executed_at:
                        logger.info("[%s] Cache was expired, so remove existing artifact.", funcinfo.name)
                        storage.remove(key)
                        storage.remove(metakey)

                if _cache_exists(key):
                    logger.info("[%s] Cache exists", funcinfo.name)
                    if asyncio.iscoroutinefunction(func):
                        return _coro_wrapper(key, metakey, execinfo, executed_at)
                    else:
                        return _load_cache(key)
                else:
                    logger.info("[%s] Cache does not exists.", funcinfo.name)
                    artifact = func(*args, **kwargs)
                    if isinstance(artifact, types.CoroutineType):
                        return _coro_wrapper(key, metakey, execinfo, executed_at, artifact)

                    _save_cache(key, metakey, execinfo, executed_at, artifact)

                    if asyncio.iscoroutinefunction(artifact):
                        return _coro_wrapper(key, metakey, execinfo, executed_at, artifact)

                    return _load_cache(key)

            @wraps(func)
            async def asyncgen_wrapper(*args: Any, **kwargs: Any) -> Any:
                assert inspect.isasyncgenfunction(func)
                executed_at = datetime.datetime.now()
                disable = self.disable if function_settings.disable is None else function_settings.disable

                storage = self.storage

                if disable:
                    logger.info("[%s] Disable cache.", funcinfo.name)
                    async for value in func(*args, **kwargs):
                        yield value
                else:
                    execinfo = ExecutionInfo.build(func, *args, **kwargs)
                    for paramname in function_settings.ignore:
                        del execinfo.params[paramname]

                    key = self._get_key(funcinfo, execinfo)
                    metakey = self._get_metakey(key)

                    if storage.exists(metakey):
                        with storage.open(metakey, "rt") as file:
                            cacheinfo = CacheInfo.from_dict(json.load(file))
                        if cacheinfo.expired_at is not None and cacheinfo.expired_at <= executed_at:
                            logger.info("[%s] Cache was expired, so remove existing artifact.", funcinfo.name)
                            storage.remove(key)
                            storage.remove(metakey)

                    if _cache_exists(key):
                        logger.info("[%s] Cache exists", funcinfo.name)
                        artifact = _load_cache(key)
                    else:
                        logger.info("[%s] Cache does not exists.", funcinfo.name)
                        results = async_to_sync_iterator(func(*args, **kwargs))

                        _save_cache(key, metakey, execinfo, executed_at, results)  # type: ignore[arg-type]

                        # reopen artifact beacause if artifact is iterator,
                        # it is consumed when saving cache.
                        artifact = _load_cache(key)

                    assert isinstance(artifact, Iterable)
                    for result in artifact:
                        yield result

            setattr(wrapper, "__signature__", inspect.signature(func))
            setattr(wrapper, "__annotations__", func.__annotations__)
            setattr(wrapper, "__cachesore_funcinfo", funcinfo)

            if inspect.isasyncgenfunction(func):
                return cast(F, asyncgen_wrapper)

            return cast(F, wrapper)

        return cast(Callable[[F], F], decorator)

    def exists(self, func: Callable[..., Any] | FunctionInfo) -> bool:
        current = datetime.datetime.now()
        exists = False
        for _, cacheinfo in self.info(func):
            exists |= cacheinfo.expired_at is None or cacheinfo.expired_at > current
        return exists

    def remove(
        self,
        func: Callable[..., Any] | FunctionInfo,
        execution_prefix: str | None = None,
    ) -> None:
        if not isinstance(func, FunctionInfo):
            func = FunctionInfo.build(func)
        prefix = func.hash(self.hasher)
        if execution_prefix is not None:
            prefix = f"{prefix}.{execution_prefix}"
        for key in self.storage.filter(prefix=prefix):
            self.storage.remove(key)

    def funcinfos(self) -> list[FunctionInfo]:
        return list(self._function_registry.values())

    def info(self, func: Callable[..., Any] | FunctionInfo) -> Iterator[tuple[str, CacheInfo]]:
        if not isinstance(func, FunctionInfo):
            func = FunctionInfo.build(func)
        prefix = func.hash(self.hasher)
        for key in self.storage.filter(prefix=prefix):
            metakey = self._get_metakey(key)
            with self.storage.open(metakey, "rt") as file:
                yield key, CacheInfo.from_dict(json.load(file))

    def prune(self) -> None:
        for key in self.storage.all():
            if not any(key.startswith((funchash, self._get_metakey(funchash))) for funchash in self._function_registry):
                logger.info("remove %s", key)
                self.storage.remove(key)

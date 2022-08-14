from __future__ import annotations

import configparser
import dataclasses
import datetime
import importlib
import os
from logging import getLogger
from os import PathLike
from pathlib import Path
from typing import Any, TypeVar

from cachestore.formatters import Formatter, PickleFormatter
from cachestore.hashers import Hasher, PickleHasher
from cachestore.storages import LocalStorage, Storage

DEFAULT_CACHE_DIR = ".cachestore"
DISABLE_CACHE = os.environ.get("CACHESTORE_DISABLE", "0").lower() in ("1", "true")

logger = getLogger(__name__)


T = TypeVar("T")


@dataclasses.dataclass
class CacheSettings:
    storage: Storage = dataclasses.field(default_factory=lambda: LocalStorage(DEFAULT_CACHE_DIR))
    formatter: Formatter = dataclasses.field(default_factory=lambda: PickleFormatter())
    hasher: Hasher = dataclasses.field(default_factory=lambda: PickleHasher())
    disable: bool = DISABLE_CACHE


@dataclasses.dataclass
class FunctionSettings:
    ignore: set[str] = dataclasses.field(default_factory=set)
    expire: int | datetime.timedelta | datetime.date | datetime.datetime | None = None
    disable: bool = False

    @property
    def expired_at(self) -> datetime.datetime | None:
        if isinstance(self.expire, int):
            expired_at = datetime.datetime.now() + datetime.timedelta(days=self.expire)
        elif isinstance(self.expire, datetime.timedelta):
            expired_at = datetime.datetime.now() + self.expire
        elif isinstance(self.expire, datetime.datetime):
            expired_at = self.expire
        elif isinstance(self.expire, datetime.date):
            expired_at = datetime.datetime(
                year=self.expire.year,
                month=self.expire.month,
                day=self.expire.day,
            )
        else:
            expired_at = None
        return expired_at


class Config:
    def __init__(self, filename: str | PathLike | None = None) -> None:
        self._parser = configparser.ConfigParser()
        self._cache_settings: dict[str, CacheSettings] = {}
        self._function_settings: dict[str, FunctionSettings] = {}

        filenames: list[Path] = []
        if filename:
            filenames.append(Path(filename))
        if filename := os.environ.get("CACHESTORE_CONFIG_PATH"):
            filenames.append(Path(filename))
        filenames.append(Path.cwd() / "cachestore.ini")

        for filename in filenames:
            if filename.exists():
                logger.info("Load config from %s", filename)
                self._parser.read(filename)

        # load cache instances
        for section in self._parser.sections():
            if self._is_function_section(section):
                self._function_settings[section] = self._load_function_settings(self._parser[section])
            else:
                self._cache_settings[section] = self._load_cache_settings(self._parser[section])

    def cache_settings(self, name: str) -> CacheSettings:
        if name not in self._cache_settings:
            self._cache_settings[name] = CacheSettings()
        return self._cache_settings[name]

    def function_settings(self, name: str) -> FunctionSettings:
        if name not in self._function_settings:
            self._function_settings[name] = FunctionSettings()
        return self._function_settings[name]

    def _is_function_section(self, name: str) -> bool:
        return " " in name

    def _load_cache_settings(self, config: configparser.SectionProxy) -> CacheSettings:
        settings = CacheSettings()
        if "storage" in config:
            storagecls = self._import_from_path(config["storage"])
            assert issubclass(storagecls, Storage)
            settings.storage = storagecls.from_config(config)
        if "formatter" in config:
            formattercls = self._import_from_path(config["formatter"])
            assert issubclass(formattercls, Formatter)
            settings.formatter = formattercls.from_config(config)
        if "hasher" in config:
            hashercls = self._import_from_path(config["hasher"])
            assert issubclass(hashercls, Hasher)
            settings.hasher = hashercls.from_config(config)
        settings.disable = config.getboolean("disable", settings.disable)
        return settings

    def _load_function_settings(self, config: configparser.SectionProxy) -> FunctionSettings:
        settings = FunctionSettings()
        if "ignore" in config:
            settings.ignore = set(x.strip() for x in config["ignore"].split(","))
        if "expire" in config:
            settings.expire = datetime.datetime.fromisoformat(config["expire"])
        if "disable" in config:
            settings.disable = config.getboolean("disable", settings.disable)
        return settings

    @staticmethod
    def _import_from_path(path: str) -> Any:
        if "." not in path and ":" in path:
            raise ValueError("Cache name must be formatted as path.to.module:name.")
        if ":" in path:
            modulename, objname = path.rsplit(":", 1)
        else:
            modulename, objname = path.rsplit(".", 1)
        module = importlib.import_module(modulename)
        return getattr(module, objname)

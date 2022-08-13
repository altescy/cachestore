from __future__ import annotations

import configparser
import dataclasses
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


class Config:
    def __init__(self, filename: str | PathLike | None = None) -> None:
        self._parser = configparser.ConfigParser()
        self._settings: dict[str, CacheSettings] = {}

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
            settings = self._load_cache_settings(self._parser[section])
            self._settings[section] = settings

    def settings(self, name: str) -> CacheSettings:
        if name not in self._settings:
            self._settings[name] = CacheSettings()
        return self._settings[name]

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

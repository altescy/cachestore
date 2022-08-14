from __future__ import annotations

import os
from configparser import SectionProxy
from contextlib import contextmanager
from os import PathLike
from pathlib import Path
from typing import IO, Any, Callable, ContextManager, Iterator, Type, TypeVar

from cachestore.common import FileLock
from cachestore.storages.storage import Storage
from cachestore.util import safe_import_object

DEFAULT_ROOT_DIR = ".cachestore"

Self = TypeVar("Self", bound="LocalStorage")


class LocalStorage(Storage):
    def __init__(
        self,
        root: str | PathLike | None = None,
        openfn: Callable[..., IO[Any]] | Callable[..., ContextManager[IO[Any]]] | None = None,
    ) -> None:
        self._root = Path(root or DEFAULT_ROOT_DIR).absolute()
        self._openfn = openfn or open

    def __str__(self) -> str:
        return f"LocalStorage(root={self._root.relative_to(Path.cwd())})"

    def __repr__(self) -> str:
        return f"LocalStorage(root={self._root.relative_to(Path.cwd())})"

    @contextmanager
    def open(self, key: str, mode: str) -> Iterator[IO[Any]]:
        filename = self._root / key
        lockfile = filename.parent / (filename.name + ".lock")
        filename.parent.mkdir(parents=True, exist_ok=True)
        with FileLock(lockfile):
            try:
                with self._openfn(filename, mode) as fp:
                    yield fp
            except (Exception, KeyboardInterrupt):
                os.remove(filename)
                raise
            finally:
                os.remove(lockfile)

    def remove(self, key: str) -> None:
        filename = self._root / key
        os.remove(filename)

    def exists(self, key: str) -> bool:
        return (self._root / key).exists()

    def all(self) -> Iterator[str]:
        for filename in self._root.glob("*"):
            yield filename.name

    def filter(self, prefix: str) -> Iterator[str]:
        for filename in self._root.glob(f"{prefix}*"):
            yield filename.name

    @classmethod
    def from_config(cls: Type[Self], config: SectionProxy) -> Self:
        root = config.get("storage.root")

        if "storage.openfn" in config:
            openfn = safe_import_object(config["storage.openfn"])
        else:
            openfn = None

        return cls(root=root, openfn=openfn)

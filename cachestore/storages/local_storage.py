from __future__ import annotations

import os
from contextlib import contextmanager
from os import PathLike
from pathlib import Path
from typing import IO, Any, Iterator

from cachestore.common import FileLock
from cachestore.storages.storage import Storage


class LocalStorage(Storage):
    def __init__(self, root: str | PathLike | None = None) -> None:
        self._root = Path(root or Path.cwd()).absolute()

        self._root.mkdir(parents=True, exist_ok=True)

    def __str__(self) -> str:
        return f"LocalStorage(root={self._root.relative_to(Path.cwd())})"

    @contextmanager
    def open(self, key: str, mode: str) -> Iterator[IO[Any]]:
        filename = self._root / key
        lockfile = filename.parent / (filename.name + ".lock")
        filename.parent.mkdir(parents=True, exist_ok=True)
        with FileLock(lockfile):
            try:
                with open(filename, mode) as fp:
                    yield fp
            except (Exception, KeyboardInterrupt):
                os.remove(filename)
                raise

    def remove(self, key: str) -> None:
        filename = self._root / key
        os.remove(filename)

    def exists(self, key: str) -> bool:
        return Path(key).exists()

    def all(self) -> Iterator[str]:
        for filename in self._root.glob("*"):
            if not filename.name.endswith(".lock"):
                yield filename.name

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

    @contextmanager
    def open(self, location: str, mode: str) -> Iterator[IO[Any]]:
        filename = Path(location)
        lockfile = filename.parent / (filename.name + ".lock")
        filename.parent.mkdir(parents=True, exist_ok=True)
        with FileLock(lockfile):
            try:
                with open(filename, mode) as fp:
                    yield fp
            except (Exception, KeyboardInterrupt):
                os.remove(filename)
                raise

    def exists(self, location: str) -> bool:
        return Path(location).exists()

    def get_artifact_location(self, funchash: str, exechash: str) -> str:
        return str(self._root / funchash / exechash)

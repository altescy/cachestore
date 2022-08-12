import abc
from contextlib import contextmanager
from typing import IO, Any, Iterator


class Storage(abc.ABC):
    @abc.abstractmethod
    @contextmanager
    def open(self, location: str, mode: str) -> Iterator[IO[Any]]:
        raise NotImplementedError

    @abc.abstractmethod
    def exists(self, location: str) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def get_artifact_location(self, funchash: str, exechash: str) -> str:
        raise NotImplementedError

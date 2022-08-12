import abc
from contextlib import contextmanager
from typing import IO, Any, Iterator


class Storage(abc.ABC):
    @abc.abstractmethod
    @contextmanager
    def open(self, key: str, mode: str) -> Iterator[IO[Any]]:
        raise NotImplementedError

    @abc.abstractmethod
    def exists(self, key: str) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def remove(self, key: str) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def all(self) -> Iterator[str]:
        raise NotImplementedError

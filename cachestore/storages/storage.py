import abc
from configparser import SectionProxy
from contextlib import contextmanager
from typing import IO, Any, Iterator, Type, TypeVar

Self = TypeVar("Self", bound="Storage")


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

    @classmethod
    def from_config(cls: Type[Self], config: SectionProxy) -> Self:
        raise NotImplementedError

    def filter(self, prefix: str) -> Iterator[str]:
        for key in self.all():
            if key.startswith(prefix):
                yield key

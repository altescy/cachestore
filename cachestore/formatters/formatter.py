import abc
from configparser import SectionProxy
from typing import IO, Any, ClassVar, Type, TypeVar

Self = TypeVar("Self", bound="Formatter")


class Formatter(abc.ABC):
    READ_MODE: ClassVar[str]
    WRITE_MODE: ClassVar[str]

    @abc.abstractmethod
    def write(self, file: IO[Any], obj: Any) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def read(self, file: IO[Any]) -> Any:
        raise NotImplementedError

    @classmethod
    def from_config(cls: Type[Self], config: SectionProxy) -> Self:
        raise NotImplementedError

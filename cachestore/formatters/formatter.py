import abc
from typing import IO, Any, ClassVar


class Formatter(abc.ABC):
    READ_MODE: ClassVar[str]
    WRITE_MODE: ClassVar[str]

    @abc.abstractmethod
    def write(self, file: IO[Any], obj: Any) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def read(self, file: IO[Any]) -> Any:
        raise NotImplementedError

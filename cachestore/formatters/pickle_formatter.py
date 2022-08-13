import pickle
from configparser import SectionProxy
from typing import IO, Any, ClassVar, Type, TypeVar

from cachestore.formatters.formatter import Formatter

Self = TypeVar("Self", bound="PickleFormatter")


class PickleFormatter(Formatter):
    READ_MODE: ClassVar = "rb"
    WRITE_MODE: ClassVar = "wb"

    def write(self, file: IO[Any], obj: Any) -> None:
        pickle.dump(obj, file)

    def read(self, file: IO[Any]) -> Any:
        return pickle.load(file)

    @classmethod
    def from_config(cls: Type[Self], config: SectionProxy) -> Self:
        return cls()

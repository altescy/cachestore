import pickle
from typing import IO, Any, ClassVar

from cachestore.formatters.formatter import Formatter


class PickleFormatter(Formatter):
    READ_MODE: ClassVar = "rb"
    WRITE_MODE: ClassVar = "wb"

    def write(self, file: IO[Any], obj: Any) -> None:
        pickle.dump(obj, file)

    def read(self, file: IO[Any]) -> Any:
        return pickle.load(file)

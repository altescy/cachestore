from __future__ import annotations

import pickle
from configparser import SectionProxy
from typing import IO, Any, ClassVar, Iterator, Type, TypeVar

from cachestore.formatters.formatter import Formatter
from cachestore.util import detect_open_fn

Self = TypeVar("Self", bound="PickleFormatter")


class PickleFormatIterator:
    def __init__(self, file: IO[Any]):
        self.file: IO[Any] | None = None

        # Reopen file by detecting the open function.  This is workaround
        # for the fact that the file is closed. Be aware that this may not
        # work for all file-like objects.
        open_fn = detect_open_fn(file)
        self.file = open_fn(file.name, file.mode)

        # Validate that the file is an iterator.
        is_iterator = pickle.load(self.file)
        if not is_iterator:
            raise ValueError(f"File is not an iterator: {file.name}")

    def __iter__(self) -> Iterator[Any]:
        return self

    def __next__(self) -> Any:
        if self.file is None:
            raise StopIteration
        try:
            return pickle.load(self.file)
        except EOFError:
            self.file.close()
            self.file = None
            raise StopIteration


class PickleFormatter(Formatter):
    READ_MODE: ClassVar = "rb"
    WRITE_MODE: ClassVar = "wb"

    def write(self, file: IO[Any], obj: Any) -> None:
        if hasattr(obj, "__next__"):
            pickle.dump(True, file)
            for item in obj:
                pickle.dump(item, file)
        else:
            pickle.dump(False, file)
            pickle.dump(obj, file)

    def read(self, file: IO[Any]) -> Any:
        is_iterator = pickle.load(file)
        if is_iterator:
            return PickleFormatIterator(file)
        return pickle.load(file)

    @classmethod
    def from_config(cls: Type[Self], config: SectionProxy) -> Self:
        return cls()

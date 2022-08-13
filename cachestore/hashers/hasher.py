from __future__ import annotations

import abc
from configparser import SectionProxy
from typing import Any, Type, TypeVar

Self = TypeVar("Self", bound="Hasher")


class Hasher(abc.ABC):
    @abc.abstractmethod
    def __call__(self, obj: Any) -> str:
        raise NotImplementedError

    @classmethod
    def from_config(cls: Type[Self], config: SectionProxy) -> Self:
        raise NotImplementedError

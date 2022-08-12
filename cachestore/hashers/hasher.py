from __future__ import annotations

import abc
from typing import Any


class Hasher(abc.ABC):
    @abc.abstractmethod
    def __call__(self, obj: Any) -> str:
        raise NotImplementedError

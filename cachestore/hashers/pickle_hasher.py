import hashlib
import io
import pickle
from configparser import SectionProxy
from typing import Any, Type, TypeVar

from cachestore.hashers.hasher import Hasher
from cachestore.util import b62encode

Self = TypeVar("Self", bound="Hasher")


class PickleHasher(Hasher):
    def __call__(self, obj: Any) -> str:
        m = hashlib.blake2b()
        with io.BytesIO() as buf:
            pickle.dump(obj, buf)
            m.update(buf.getbuffer())
            return b62encode(m.digest())

    @classmethod
    def from_config(cls: Type[Self], config: SectionProxy) -> Self:
        return cls()

import hashlib
import io
import pickle
from typing import Any

from cachestore.hashers.hasher import Hasher
from cachestore.util import b62encode


class PickleHasher(Hasher):
    def __call__(self, obj: Any) -> str:
        m = hashlib.blake2b()
        with io.BytesIO() as buf:
            pickle.dump(obj, buf)
            m.update(buf.getbuffer())
            return b62encode(m.digest())

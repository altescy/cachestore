from __future__ import annotations

import json
import logging
from configparser import SectionProxy
from typing import IO, Any, ClassVar

from cachestore import Cache, Formatter

logging.basicConfig(level=logging.INFO)


class JsonFormatter(Formatter):
    READ_MODE: ClassVar = "rt"
    WRITE_MODE: ClassVar = "wt"

    def write(self, file: IO[Any], obj: Any) -> None:
        json.dump(obj, file)

    def read(self, file: IO[Any]) -> Any:
        return json.load(file)

    @classmethod
    def from_config(cls, config: SectionProxy) -> "JsonFormatter":
        return cls()


cache = Cache()


@cache()
def square(x: int) -> int:
    print(f"square is executed with {x}")
    return x * x


@cache(expire=-1)
def expired_square(x: int) -> int:
    print(f"expired_square is executed with {x}")
    return x * x


@cache(ignore={"y"})
def ignored_square(x: int, y: int) -> int:
    print(f"ignored_square is executed with {x=} ignoring {y=}")
    return x * x


@cache(disable=True)
def disabled_square(x: int) -> int:
    print(f"disabled_square is executed with {x}, this result is never cached")
    return x * x


@cache()
def ignored_square_from_config(x: int, y: int) -> int:
    print(f"ignored_square_from_config is executed with {x=} ignoring {y=}")
    return x * x


@cache()
def disabled_square_from_config(x: int) -> int:
    print(f"disabled_square_from_config is executed with {x}, this result is never cached")
    return x * x


@cache(formatter=JsonFormatter())
def json_formatted_square(x: int) -> dict[str, int]:
    print("json_formatted_square_from_comfing is executed and the result will be formatted as JSON.")
    return {"result": x * x}


@cache()
def json_formatted_square_from_comfing(x: int) -> dict[str, int]:
    print("json_formatted_square_from_comfing is executed and the result will be formatted as JSON.")
    return {"result": x * x}


if __name__ == "__main__":
    print(f"{cache.name=}")
    print(f"{cache.settings=}")

    print(f"{square(2)=}")
    print(f"{square(2)=}")
    print(f"{square(3)=}")
    print(f"{expired_square(2)=}")
    print(f"{expired_square(2)=}")
    print(f"{ignored_square(2, 3)=}")
    print(f"{ignored_square(2, 4)=}")
    print(f"{disabled_square(2)=}")
    print(f"{disabled_square(2)=}")
    print(f"{ignored_square_from_config(2, 3)=}")
    print(f"{ignored_square_from_config(2, 4)=}")
    print(f"{disabled_square_from_config(2)=}")
    print(f"{disabled_square_from_config(2)=}")
    print(f"{json_formatted_square(2)=}")
    print(f"{json_formatted_square_from_comfing(2)=}")

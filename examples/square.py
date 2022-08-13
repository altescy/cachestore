import logging

from cachestore import Cache

logging.basicConfig(level=logging.INFO)

cache = Cache()


@cache()
def square(x: int) -> int:
    print(f"square is executed with {x}!")
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

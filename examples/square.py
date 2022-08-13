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


if __name__ == "__main__":
    print(f"{square(2)=}")
    print(f"{square(2)=}")
    print(f"{square(3)=}")
    print(f"{expired_square(2)=}")
    print(f"{expired_square(2)=}")

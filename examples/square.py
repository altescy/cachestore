from cachestore import Cache

cache = Cache()


@cache()
def square(x: int) -> int:
    print(f"square is executed with {x}")
    return x * x


if __name__ == "__main__":
    print(square(2))

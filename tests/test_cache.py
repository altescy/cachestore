from pathlib import Path
from typing import Iterator

from cachestore import Cache, LocalStorage


def test_cache(tmp_path: Path) -> None:
    cache_root = tmp_path / "cache"
    cache = Cache("testcache", storage=LocalStorage(cache_root))

    @cache()
    def square(x: int) -> int:
        return x * x

    output_1 = square(2)
    assert cache.exists(square)

    output_2 = square(2)
    assert output_1 == output_2 == 4


def test_iterator_cache(tmp_path: Path) -> None:
    cache_root = tmp_path / "cache"
    cache = Cache("testcache", storage=LocalStorage(cache_root))

    @cache()
    def gen(n: int) -> Iterator[int]:
        yield from range(n)

    output_1 = gen(5)
    assert cache.exists(gen)

    output_2 = gen(5)
    assert list(output_1) == list(output_2) == [0, 1, 2, 3, 4]

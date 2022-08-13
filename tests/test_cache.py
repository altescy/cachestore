from pathlib import Path

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

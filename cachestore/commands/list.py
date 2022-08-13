import argparse
import importlib

from cachestore.commands.subcommand import Subcommand
from cachestore.common import Table
from cachestore.util import import_modules


@Subcommand.register("list")
class ListCommand(Subcommand):
    def setup(self) -> None:
        self.parser.add_argument("cache", nargs="+")
        self.parser.add_argument("--include-package", action="append", default=[])

    def run(self, args: argparse.Namespace) -> None:
        if args.include_package:
            import_modules(args.include_package)

        for cache_path in args.cache:
            cache_module, cache_name = cache_path.split(":", 1)
            cache = getattr(importlib.import_module(cache_module), cache_name)

            table = Table(columns=["name", "function", "cache", "last_executed_at"])
            for funcinfo in cache.funcinfos():
                cacheinfos = list(cache.info(funcinfo))
                table.add(
                    {
                        "name": cache_path,
                        "function": funcinfo.name,
                        "cache": "✓" if cache.exists(funcinfo) else "",
                        "last_executed_at": max(info.executed_at for info in cacheinfos).isoformat(),
                    }
                )

        table.show()

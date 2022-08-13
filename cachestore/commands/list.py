import argparse
import datetime
import importlib
from pathlib import Path

from cachestore.cache import Cache
from cachestore.commands.subcommand import Subcommand
from cachestore.common import Selector, Table
from cachestore.util import import_modules


@Subcommand.register("list")
class ListCommand(Subcommand):
    def setup(self) -> None:
        self.parser.add_argument("cache")
        self.parser.add_argument("--include-package", action="append", default=[])

    def run(self, args: argparse.Namespace) -> None:
        if args.include_package:
            import_modules(args.include_package)

        cache_module, cache_name = args.cache.split(":", 1)
        cache = getattr(importlib.import_module(cache_module), cache_name)

        table = Table(columns=["name", "function", "filename", "cache", "last_executed_at"])
        for funcinfo in cache.funcinfos():
            cacheinfos = list(cache.info(funcinfo))
            table.add(
                {
                    "name": args.cache,
                    "function": funcinfo.name,
                    "filename": str(funcinfo.filename.relative_to(Path.cwd())),
                    "cache": "\033[32m✓\033[39m" if cache.exists(funcinfo) else "",
                    "last_executed_at": max(info.executed_at for info in cacheinfos).strftime("%Y-%m-%d %H:%M:%S")
                    if cacheinfos
                    else "",
                }
            )

        table.sort("last_executed_at", desc=True)
        table.show()


@ListCommand.register("details")
class DetailsCommand(ListCommand):
    def setup(self) -> None:
        self.parser.add_argument("-f", "--function", default=None)

    def run(self, args: argparse.Namespace) -> None:
        if args.include_package:
            import_modules(args.include_package)

        table = Table(columns=["cache", "function", "filename", "params", "executed_at", "expired_at"])

        cache_module, cache_name = args.cache.split(":", 1)
        cache = getattr(importlib.import_module(cache_module), cache_name)
        assert isinstance(cache, Cache)

        funcinfos = {info.name: info for info in cache.funcinfos()}

        if args.function:
            funcname = args.function
        else:
            funcname = Selector()(list(funcinfos))

        if not funcname or funcname not in funcinfos:
            print("No information to show.")
            return

        funcinfo = funcinfos[funcname]

        for cacheinfo in cache.info(funcinfo):
            table.add(
                {
                    "cache": args.cache,
                    "function": funcinfo.name,
                    "filename": str(funcinfo.filename.relative_to(Path.cwd())),
                    "params": ", ".join(f"{k}={v}" for k, v in cacheinfo.parameters.items()),
                    "executed_at": cacheinfo.executed_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "expired_at": (
                        cacheinfo.expired_at.strftime("%Y-%m-%d %H:%M:%S")
                        if cacheinfo.expired_at > datetime.datetime.now()
                        else f"\033[31m{cacheinfo.expired_at.strftime('%Y-%m-%d %H:%M:%S')}\033[39m"
                    )
                    if cacheinfo.expired_at
                    else "",
                }
            )

        table.sort("executed_at", desc=True)
        table.show()

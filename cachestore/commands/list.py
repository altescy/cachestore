import argparse
import datetime
import sys
from pathlib import Path

from cachestore.cache import Cache
from cachestore.commands.subcommand import Subcommand
from cachestore.common import Selector, Table
from cachestore.util import import_modules, safe_import_object


@Subcommand.register("list")
class ListCommand(Subcommand):
    """list functions and cache statuses"""

    def setup(self) -> None:
        self.parser.add_argument(
            "cache",
            help="cache name",
        )
        self.parser.add_argument(
            "--include-package",
            action="append",
            default=[],
            help="additinoal packages to include",
        )

    def run(self, args: argparse.Namespace) -> None:
        if args.include_package:
            import_modules(args.include_package)

        cache = Cache.by_name(args.cache)
        if cache is None:
            cache = safe_import_object(args.cache)

        if cache is None:
            print(f"Given cache name is not found: {args.cache}", file=sys.stderr)
            sys.exit(1)

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
    """list cache status details of specified function"""

    def setup(self) -> None:
        self.parser.add_argument(
            "-f",
            "--function",
            default=None,
            help="function name to show details",
        )

    def run(self, args: argparse.Namespace) -> None:
        if args.include_package:
            import_modules(args.include_package)

        table = Table(columns=["cache", "function", "filename", "params", "executed_at", "expired_at"])

        cache = safe_import_object(args.cache)
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

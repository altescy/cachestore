import argparse
import importlib
import sys

from cachestore.cache import Cache
from cachestore.commands.subcommand import Subcommand
from cachestore.util import import_modules


@Subcommand.register("prune")
class PruneCommand(Subcommand):
    def setup(self) -> None:
        self.parser.add_argument("cache")
        self.parser.add_argument("--include-package", action="append", default=[])

    def run(self, args: argparse.Namespace) -> None:
        if args.include_package:
            import_modules(args.include_package)

        cache = Cache.by_name(args.cache)
        if cache is None and ":" in args.cache:
            cache_module, cache_name = args.cache.split(":", 1)
            cache = getattr(importlib.import_module(cache_module), cache_name, None)

        if cache is None:
            print(f"Given cache name is not found: {args.cache}", file=sys.stderr)
            sys.exit(1)

        cache.prune()

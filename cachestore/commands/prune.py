import argparse
import sys

from cachestore.cache import Cache
from cachestore.commands.subcommand import Subcommand
from cachestore.util import import_modules, safe_import_object


@Subcommand.register("prune")
class PruneCommand(Subcommand):
    """prune unreferenced caches"""

    def setup(self) -> None:
        self.parser.add_argument("cache", help="cache name")
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

        cache.prune()

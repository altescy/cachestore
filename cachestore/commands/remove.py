import argparse
import sys

from cachestore.cache import Cache
from cachestore.commands.subcommand import Subcommand
from cachestore.common import Selector
from cachestore.util import import_modules, safe_import_object


@Subcommand.register("remove")
class RemoveCommand(Subcommand):
    """remove caches"""

    def setup(self) -> None:
        self.parser.add_argument("cache", help="cache name")
        self.parser.add_argument(
            "-f",
            "--function",
            action="append",
            default=[],
            help="function names to remove cache formatted like: function[@exec]",
        )
        self.parser.add_argument(
            "-a",
            "--all",
            action="store_true",
            help="remove all caches of the specified cache",
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

        funcinfos = {funcinfo.name: funcinfo for funcinfo in cache.funcinfos() if cache.exists(funcinfo)}
        if args.all:
            funcnames = set(funcinfos.keys())
        elif args.function:
            funcnames = set(args.function)
        else:
            funcnames = set()
            candidates = [name for name in funcinfos.keys()]
            if candidates:
                selected_funcname = Selector()(candidates)
                funcnames = set() if selected_funcname is None else {selected_funcname}

        if funcnames:
            for funcname in funcnames:
                if "@" in funcname:
                    parsed_funcname, execution_prefix = funcname.split("@", 1)
                else:
                    parsed_funcname = funcname
                    execution_prefix = None
                if args.all or parsed_funcname in funcinfos:
                    print(f"remove: {funcname}")
                    cache.remove(funcinfos[parsed_funcname], execution_prefix=execution_prefix)
                else:
                    print(f"skip  : {funcname}")
        else:
            print("No caches to remove.")

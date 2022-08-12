import argparse
import importlib

from cachestore.commands.subcommand import Subcommand
from cachestore.common import Selector
from cachestore.util import import_modules


@Subcommand.register("remove")
class RemoveCommand(Subcommand):
    def setup(self) -> None:
        self.parser.add_argument("cache")
        self.parser.add_argument("-f", "--function", action="append", default=[])
        self.parser.add_argument("-a", "--all", action="store_true")
        self.parser.add_argument("--include-package", action="append", default=[])

    def run(self, args: argparse.Namespace) -> None:
        if args.include_package:
            import_modules(args.include_package)

        cache_module, cache_name = args.cache.split(":", 1)
        cache = getattr(importlib.import_module(cache_module), cache_name)

        funcinfos = {funcinfo.name: funcinfo for funcinfo in cache.funcinfos() if cache.exists(funcinfo)}
        if args.all:
            funcnames = set(funcinfos.keys())
        elif args.function:
            funcnames = set(args.function)
        else:
            funcnames = set()
            candidates = [name for name, info in funcinfos.items()]
            if candidates:
                selected_funcname = Selector()(candidates)
                funcnames = set() if selected_funcname is None else {selected_funcname}

        if funcnames:
            for funcname in funcnames:
                if args.all or funcname in funcinfos:
                    print(f"remove: {funcname}")
                    cache.remove(funcinfos[funcname])
                else:
                    print(f"skip  : {funcname}")
        else:
            print("No caches to remove.")

from __future__ import annotations

import argparse

from cachestore import __version__
from cachestore.commands import list as _list  # noqa: F401
from cachestore.commands import remove  # noqa: F401
from cachestore.commands.subcommand import Subcommand


def create_subcommand(prog: str | None = None) -> Subcommand:
    parser = argparse.ArgumentParser(usage="%(prog)s", prog=prog)
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s " + __version__,
    )
    return Subcommand(parser)


def main(prog: str | None = None) -> None:
    app = create_subcommand(prog)
    app()

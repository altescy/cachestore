import logging
import os

from cachestore.commands import main

if os.environ.get("CACHESTORE_DEBUG"):
    LEVEL = logging.DEBUG
else:
    level_name = os.environ.get("CACHESTORE_LOG_LEVEL", "WARNING")
    LEVEL = logging._nameToLevel.get(level_name, logging.WARNING)

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(name)s - %(message)s", level=LEVEL)


def run() -> None:
    main(prog="cachestore")


if __name__ == "__main__":
    run()

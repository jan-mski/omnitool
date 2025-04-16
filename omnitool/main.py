import logging
import sys

from omnitool import settings
from omnitool.plugin import loader


logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(stream=sys.stdout)
    ]
)


def main(args):
    logger.info("Starting omnitool")
    settings.load_settings()
    loader.load_plugins()

    if not loader.loaded_plugins:
        logger.error("No plugins loaded, exiting")
        return

    logger.info("Omnitool started")


if __name__ == "__main__":
    main(sys.argv)

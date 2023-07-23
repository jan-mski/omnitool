import logging
import sys

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
    loader.load_plugins()


if __name__ == "__main__":
    main(sys.argv)

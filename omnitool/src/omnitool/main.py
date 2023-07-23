import logging
import sys

from plugin import loader


logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(stream=sys.stdout)
    ]
)


if __name__ == "__main__":
    loader.load_plugins()

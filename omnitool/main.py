import logging
import os
import sys

from omnitool import settings, cli
from omnitool.plugin.loading import loader


logger = logging.getLogger(__name__)


debug_enabled = os.environ.get("DEBUG", "").lower() in ["true", "1", "yes", "y", "on", "enable", "enabled"]
log_level = logging.DEBUG if debug_enabled else logging.INFO

logging.basicConfig(
    level=log_level,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(stream=sys.stdout)],
)


def initialize_app():
    settings.load_settings()
    loader.load_plugins()
    cli.initialize_operations()


# Init app here for CLI completion to work
initialize_app()

# Note: this code is not executed when running from CLI, cli.app() is called directly as per pyproject.toml
if __name__ == "__main__":
    cli.app()

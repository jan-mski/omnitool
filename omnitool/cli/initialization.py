import logging
from typer import Typer

from omnitool.plugin.loading import loader
from omnitool.plugin.loading.loader import LoadedPlugin
from omnitool.cli.operation import cli_operation


app = Typer(no_args_is_help=True)
logger = logging.getLogger(__name__)


@app.callback()
def callback():
    pass  # stop Typer from setting a default command


def initialize_operations():
    """
    Initializes CLI operations for all loaded plugins.
    Creates a Typer subcommand for each plugin, and decorates operations.
    """
    for plugin in loader.loaded_plugins.values():
        plugin_app = _create_plugin_app(plugin)
        _initialize_plugin_operations(plugin, plugin_app)


def _initialize_plugin_operations(plugin: LoadedPlugin, plugin_app: Typer):
    for operation in plugin.definition.operations:
        decorated_operation = cli_operation(plugin, operation)
        plugin_app.command(decorated_operation.__name__)(decorated_operation)


def _create_plugin_app(plugin: LoadedPlugin) -> Typer:
    plugin_app = Typer()
    app.add_typer(plugin_app, name=plugin.definition.root_operation_name)
    return plugin_app

# omnitool

A plugin-based CLI tool for performing operations across multiple resources at once.

It was originally built to help a manage too many microservices - doing git operations across many repositories and releasing multiple projects in one go, without having to `cd` into every directory manually.

> **Note:** This project uses Typer, which adds noticeable startup latency. On the upside, that adds the possibility to install command line completions, so, well, there's that I guess.

## Install

```bash
cd <cloned-repository-path>
pipx install .
```

## Usage

Example using the built-in `git` plugin:

```bash
omnitool git checkout branch some-branch  # will interactively ask for context and resources

omnitool git checkout some-branch --context my-projects --resource project-1 --resource project-2  # context and resource provided

```

### App settings

Default settings will be added on first run and stored in `~/.omnitool/settings.json`.

It should look something like this:

```json
{
  "plugins": {
    "default": "git",
    "enabled": [
      "git"
    ]
  }
}
```

### Plugin configuration

Plugins store their configuration in `~/.omnitool/plugins/<plugin_name>/configuration.json`. For example, the built-in `git` plugin might be configured like this:

```json
{
  "contexts": [
    {
      "name": "my-projects",
      "resources": [
        {
          "name": "project-1",
          "uri": "file:///home/user/projects/project-1"
        },
        {
          "name": "project-2",
          "uri": "file:///home/user/projects/project-2"
        }
      ]
    }
  ]
}
```

## Available plugins

- **git** - perform git operations (e.g. `checkout`) across multiple configured repositories at once.

## Writing a plugin

Plugins are Python packages that expose a `PluginDefinition` via a setuptools entry point.

1. Create a module with a `PluginDefinition` named `definition`.

```python
from omnitool.plugin.api.context import Context
from omnitool.plugin.api.definition import PluginDefinition

class MyResource:
    pass

definition = PluginDefinition(
    root_operation_name="myplugin",
    resource_data_type=MyResource,
)

@definition.context_loader
def load_context(context: Context) -> None:
    """Load resources into the context."""

@definition.operation
def my_operation(some_arg: str, context: Context) -> None:
    """An operation that runs against every selected resource."""
```

2. Register the entry point in your `pyproject.toml`:

```toml
[project.entry-points."omnitool.plugin"]
myplugin = "my_package.plugin:definition"
```

3. Install the package into the same environment as omnitool. If using pipx, run:                               

```bash
pipx inject omnitool my-plugin-package
``` 

**Notes:**
> - `root_operation_name` becomes the Typer subcommand name.
> - Operations **must** accept a `context: Context` keyword argument.
> - `resource_data_type` can be any class; it is not strictly required to be used.

## Troubleshooting

Set the environment variable to enable debug output:

```bash
DEBUG=true omnitool
```

This will print extra diagnostic information that can help pinpoint issues with plugin loading or command execution.

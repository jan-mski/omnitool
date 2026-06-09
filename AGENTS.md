# AGENTS.md

## Repository: omnitool

A Python CLI tool with a plugin-based architecture. Built with Poetry, uses Typer + questionary for interactive CLI, and Pydantic for settings/configuration.

### Quick Commands

- **Install dependencies**: `uv install`
- **Run tests**: `uv run pytest`
- **Run CLI**: `uv run omnitool`
- **Entry point**: `omnitool.main:cli.app` (registered in `pyproject.toml`)

### Project Structure

- `omnitool/main.py` — App initialization: loads settings, finds plugins, registers CLI commands.
- `omnitool/cli/` — Typer CLI wiring and operation decorators.
- `omnitool/plugin/` — Plugin API and loading system.
- `omnitool/builtin_plugins/` — Built-in plugins (only `git` currently).
- `tests/` — Mirrors source structure. Uses `pytest-mock` and `factory-boy`.

### Plugin Architecture

- Plugins register via setuptools entry points under group `omnitool.plugin` (see `pyproject.toml`).
- Built-in plugins are defined in `omnitool/builtin_plugins/<name>/plugin.py`.
- A plugin exports a `PluginDefinition` object named `definition`.
- `PluginDefinition` requires:
  - `root_operation_name` — becomes the Typer subcommand name.
  - `resource_data_type` — any class.
  - `context_loader_function` — decorated with `@definition.context_loader`.
  - Operations decorated with `@definition.operation` — each becomes a CLI subcommand.
- Operations **must** accept a `context: Context` keyword argument. The CLI wrapper injects it after filtering resources.

### Settings & Configuration

- User settings file: `~/.omnitool/settings.json` (Pydantic Settings, auto-created with defaults).
- Default enabled plugins: `["git"]`; default plugin is the first enabled.
- Plugin configuration directory: `~/.omnitool/plugins/<plugin_name>/configuration.json`.
- Do not hardcode paths; use `omnitool.settings.OMNITOOL_HOME_PATH` and `PLUGIN_CONFIGURATIONS_PATH`.

### Testing

- Tests use heavy mocking for `questionary` interactive prompts. The `conftest.py` provides fixtures (`create_loaded_plugin`, `sample_context`, etc.) that most CLI tests depend on.
- `tests/cli/test_initialization.py` uses an `autouse` fixture that resets the global Typer app state (`app.registered_groups`, `app.registered_commands`) between tests to prevent cross-test pollution.

### Toolchain

- **Build**: uv (lockfile committed)
- **CLI**: Typer + Click + questionary
- **Settings**: pydantic-settings
- **Test**: pytest, pytest-mock, factory-boy

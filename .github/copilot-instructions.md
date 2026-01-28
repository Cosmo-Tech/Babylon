# Babylon AI Coding Instructions

You are an expert developer working on Babylon, a Python-based CLI for CosmoTech platform orchestration.

## Architecture & Patterns

### 1. The Singleton Environment
The `Environment` class ([Babylon/utils/environment.py](Babylon/utils/environment.py)) is a singleton that manages global state, configurations, and connectivity.
- **Accessing Environment**: Always use `from Babylon.utils.environment import Environment; env = Environment()`.
- **State Persistence**: State is stored in YAML files. Use `env.retrieve_state_func()` to get the current state and `env.store_state_in_local(state)` to save updates.
- **Templating**: Use `env.fill_template(data, state)` to render payloads using Mako templates.

### 2. Standard Command Structure
Commands must follow the Click framework conventions combined with Babylon's custom decorators:
- **Base Decorators**: Every command should likely use `@injectcontext()`, `@output_to_file`, and `@pass_keycloak_token()` if it interacts with the CosmoTech API.
- **Standard Return**: Functions MUST return a `CommandResponse` object ([Babylon/utils/response.py](Babylon/utils/response.py)).
- **Logic Separation**: Keep CLI argument parsing in the command function and move business logic/orchestration to a function or a macro.

Example:
```python
@group.command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
def my_command(config: dict, keycloak_token: str, **kwargs) -> CommandResponse:
    # Logic here
    return CommandResponse.success(data)
```

### 3. Macros & Orchestration
Macros ([Babylon/commands/macro/](Babylon/commands/macro/)) are for complex workflows.
- Use `env.get_ns_from_text(content=namespace)` to initialize context from a namespace string.
- Prefer idempotency: check if a resource exists in `state` before creating it, then update `state` with new IDs.

## Developer Workflows

### Build & Run
- **Installation**: Use `uv pip install -e . --group dev` for a development environment.
- **Testing**: Run `pytest tests/unit` for unit tests and `tests/e2e/test_e2e.sh` for full flow validation.
- **Formatting**: Adhere to `ruff` linting and formatting rules.

## Project Conventions
- **Naming**: Use snake_case for Python files and functions.
- **Logging**: Use the central `logger = logging.getLogger("Babylon")`. Use `rich` markup in log messages for terminal formatting (e.g., `[bold red]✘[/bold red]`).
- **Templates**: Payload templates are stored in [Babylon/templates/](Babylon/templates/) and use `${var}` or `${services.api.xxx}` syntax.
- **Error Handling**: Don't use raw `sys.exit()`. Return `CommandResponse.fail()` and let the `@output_to_file` decorator handle the `ClickException`.

## Key Files to Reference
- [Babylon/utils/environment.py](Babylon/utils/environment.py): Core state manager.
- [Babylon/utils/decorators.py](Babylon/utils/decorators.py): Common CLI decorators.
- [Babylon/utils/response.py](Babylon/utils/response.py): Command output standard.
- [Babylon/commands/api/solution.py](Babylon/commands/api/solution.py): Representative API command implementation.

## Additional Resources
If you cannot find the information you need in these instructions, refer to the following comprehensive guides:
- [Project_Architecture_Blueprint.md](Project_Architecture_Blueprint.md): For a deep dive into the system's architecture, layers, and design decisions.
- [exemplars.md](exemplars.md): For high-quality code examples demonstrating standard patterns and best practices.


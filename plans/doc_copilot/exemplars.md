# Code Exemplars: Babylon

This document identifies high-quality, representative code examples within the Babylon codebase. These exemplars demonstrate our coding standards, architectural patterns, and best practices to help developers maintain consistency while extending the CLI.

## Table of Contents
- [Python Exemplars](#python-exemplars)
- [Architecture Layer Exemplars](#architecture-layer-exemplars)
- [Cross-Cutting Concerns](#cross-cutting-concerns)
- [Testing Patterns](#testing-patterns)

---

## Python Exemplars

### Class Definitions & State Management
- **Exemplar**: [Babylon/utils/environment.py](Babylon/utils/environment.py)
- **Description**: Demonstrates the **Singleton Pattern** and centralized state management.
- **Key Principles**:
    - Uses a metaclass (`SingletonMeta`) for singleton implementation.
    - Centralizes environment variable retrieval and Kubernetes secret integration.
    - Manages state synchronization between local disk and cloud storage (Azure Blob).
- **Snippet**:
```python
class Environment(metaclass=SingletonMeta):
    def __init__(self):
        self.remote = False
        self.pwd = Path.cwd()
        # ... initialization logic
```

### API Interface Pattern
- **Exemplar**: [Babylon/commands/api/solution.py](Babylon/commands/api/solution.py)
- **Description**: A blueprint for wrapping external SDKs (CosmoTech API) into Click commands.
- **Key Principles**:
    - Clear separation between API client initialization (`get_solution_api_instance`) and command logic.
    - Consistent error handling using `try/except` blocks that return `CommandResponse.fail()`.
    - Usage of custom decorators like `@injectcontext()` and `@output_to_file`.
- **Snippet**:
```python
@solutions.command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
def create(config: dict, keycloak_token: str, organization_id: str, payload_file) -> CommandResponse:
    # ... logic for creating a solution
```

### Utility Modules & Decorators
- **Exemplar**: [Babylon/utils/decorators.py](Babylon/utils/decorators.py)
- **Description**: Demonstrates how to extend Click functionality via reusable decorators.
- **Key Principles**:
    - Use of `functools.wraps` to preserve function metadata.
    - Clean abstraction of common CLI concerns (e.g., adding an `-o/--output` flag to any command).
    - Separation of terminal formatting logic from business logic.

---

## Architecture Layer Exemplars

### Presentation Layer (CLI Interface)
- **Exemplar**: [Babylon/main.py](Babylon/main.py)
- **Description**: The entry point of the application, showing command registration and logging setup.
- **Key Details**: Uses a result callback (`interactive_run`) to enable post-command interactive sessions.

### Business Logic Layer (Macro Orchestration)
- **Exemplar**: [Babylon/commands/macro/deploy_solution.py](Babylon/commands/macro/deploy_solution.py)
- **Description**: Orchestrates complex flows involving state lookup, template rendering, and conditional API calls.
- **Key Details**: Implements "Create or Update" logic based on existing state IDs, ensuring idempotency.

### Data Access Layer (State & Files)
- **Exemplar**: [Babylon/utils/working_dir.py](Babylon/utils/working_dir.py)
- **Description**: Manages file system interactions and encryption for deployment artifacts.
- **Key Details**: Encapsulates Fernet-based encryption for sensitive data within the working directory.

---

## Cross-Cutting Concerns

### Error Handling & Standardized Responses
- **Exemplar**: [Babylon/utils/response.py](Babylon/utils/response.py)
- **Description**: Defines a standard container for command execution results.
- **Key Principles**:
    - Provides a uniform structure (`status_code`, `data`, `command`) for all outputs.
    - Automates standard terminal printing (YAML/JSON) for consistent user experience.

### Logging Implementation
- **Exemplar**: [Babylon/main.py](Babylon/main.py#L50-L90)
- **Description**: Configures `RichHandler` for beautiful terminal logs alongside standard file loggers for auditing.

---

## Testing Patterns

### Unit Testing with Pytest
- **Exemplar**: [tests/unit/test_macro.py](tests/unit/test_macro.py)
- **Description**: Comprehensive tests for internal logic functions.
- **Key Principles**:
    - Uses descriptive test names.
    - Validates both success paths and error states (e.g., `pytest.raises(Abort)`).
    - Tests complex logic like diffing ACLs and resolving inclusion/exclusion filters.

---

## Conclusion
To maintain code quality in Babylon:
1. **Always return a `CommandResponse`** from CLI commands.
2. **Use `@injectcontext()`** to automatically load configuration into your command.
3. **Persist IDs in the active state** using `Environment().store_state_in_local()` to enable command chaining.
4. **Follow the decorator patterns** in `utils/decorators.py` for adding cross-cutting flags.

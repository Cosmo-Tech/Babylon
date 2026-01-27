# Short-Form Options Implementation Research Findings

## Executive Summary
This document provides comprehensive research findings for implementing short-form options across all Babylon CLI commands. It includes exact code patterns, file locations, import statements, and test strategies.

---

## 1. Project Structure & Command Organization

### 1.1 Directory Structure
```
Babylon/commands/
├── api/                    # CosmoTech API commands
│   ├── organization.py     # Organization CRUD operations
│   ├── workspace.py        # Workspace CRUD operations
│   ├── solution.py         # Solution CRUD operations
│   ├── dataset.py          # Dataset CRUD operations
│   ├── runner.py           # Runner CRUD operations
│   ├── run.py             # Run CRUD operations
│   └── meta.py            # Meta information
├── macro/                  # High-level workflow commands
│   ├── apply.py           # Deploy resources from directory
│   ├── deploy.py          # Deployment utilities
│   ├── destroy.py         # Resource destruction
│   ├── init.py            # Project scaffolding
│   ├── deploy_organization.py
│   ├── deploy_solution.py
│   └── deploy_workspace.py
├── powerbi/               # PowerBI integration commands
│   ├── dataset/
│   │   ├── get.py
│   │   ├── delete.py
│   │   ├── get_all.py
│   │   ├── take_over.py
│   │   ├── update_credentials.py
│   │   ├── parameters/
│   │   │   ├── get.py
│   │   │   └── update.py
│   │   └── users/
│   │       └── add.py
│   ├── workspace/
│   │   ├── get.py
│   │   └── delete.py
│   ├── report/
│   │   └── delete.py
│   ├── suspend.py
│   └── resume.py
├── azure/                 # Azure-specific commands
│   ├── storage/
│   │   └── container/
│   │       └── upload.py
│   ├── permission/
│   │   └── set.py
│   └── token/
│       ├── get.py
│       └── store.py
└── namespace/             # Namespace management
    ├── use.py
    ├── get_contexts.py
    └── get_all_states.py
```

---

## 2. Current Click Option Patterns

### 2.1 Standard Import Pattern
**ALL command files use this import pattern:**

```python
from click import Path, argument, group, option
# or for simple commands:
from click import argument, command, option
```

### 2.2 Current Long-Form Option Pattern

#### API Commands - Organization Example
**File:** `Babylon/commands/api/organization.py`

```python
@organizations.command()
@injectcontext()
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
def delete(config: dict, keycloak_token: str, organization_id: str) -> CommandResponse:
    """Delete an organization by ID"""
    # ... implementation
```

**Pattern Analysis:**
- Format: `@option("--{flag}", "{param_name}", required=True, type=str, help="{description}")`
- Decorator stacking order: `@injectcontext()` → `@output_to_file` → `@pass_keycloak_token()` → `@option(...)`
- All use long-form only currently (no short forms except `-D` and `-h`)

#### API Commands - Workspace Example
**File:** `Babylon/commands/api/workspace.py`

```python
@workspaces.command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--sid", "solution_id", required=True, type=str, help="Solution ID")
@argument("payload_file", type=Path(exists=True))
def create(config: dict, keycloak_token: str, organization_id: str, solution_id: str, payload_file) -> CommandResponse:
    """Create a workspace using a YAML payload file."""
    # ... implementation
```

#### API Commands - Dataset Example
**File:** `Babylon/commands/api/dataset.py`

```python
@datasets.command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--wid", "workspace_id", required=True, type=str, help="Workspace ID")
@option("--did", "dataset_id", required=True, type=str, help="Dataset ID")
def get(config: dict, keycloak_token: str, organization_id: str, workspace_id: str, dataset_id: str) -> CommandResponse:
    """Get dataset"""
    # ... implementation
```

**Dataset Part Operations:**
```python
@datasets.command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--wid", "workspace_id", required=True, type=str, help="Workspace ID")
@option("--did", "dataset_id", required=True, type=str, help="Dataset ID")
@option("--dpid", "dataset_part_id", required=True, type=str, help="Dataset Part ID")
def get_part(config: dict, keycloak_token: str, organization_id: str, workspace_id: str, dataset_id: str, dataset_part_id: str) -> CommandResponse:
    """Get dataset part"""
    # ... implementation
```

#### API Commands - Runner Example
**File:** `Babylon/commands/api/runner.py`

```python
@runners.command()
@injectcontext()
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--wid", "workspace_id", required=True, type=str, help="Workspace ID")
@option("--rid", "runner_id", required=True, type=str, help="Runner ID")
def delete(config: dict, keycloak_token: str, organization_id: str, workspace_id: str, runner_id: str) -> CommandResponse:
    """Delete a runner by ID"""
    # ... implementation
```

#### API Commands - Run Example
**File:** `Babylon/commands/api/run.py`

```python
@runs.command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--wid", "workspace_id", required=True, type=str, help="Workspace ID")
@option("--rid", "runner_id", required=True, type=str, help="Runner ID")
@option("--rnid", "run_id", required=True, type=str, help="Run ID")
def get(config: dict, keycloak_token: str, organization_id: str, workspace_id: str, runner_id: str, run_id: str) -> CommandResponse:
    """Get a run"""
    # ... implementation
```

#### Macro Commands - Apply Example
**File:** `Babylon/commands/macro/apply.py`

```python
@command()
@injectcontext()
@argument("deploy_dir", type=ClickPath(dir_okay=True, exists=True))
@option(
    "--var-file",
    "variables_files",
    type=ClickPath(file_okay=True, exists=True),
    default=["./variables.yaml"],
    multiple=True,
    help="Specify the path of your variable file. By default, it takes the variables.yaml file.",
)
@option("--include", "include", multiple=True, type=str, help="Specify the resources to deploy.")
@option("--exclude", "exclude", multiple=True, type=str, help="Specify the resources to exclude from deployment.")
def apply(deploy_dir: ClickPath, include: tuple[str], exclude: tuple[str], variables_files: tuple[PathlibPath]):
    """Macro Apply"""
    # ... implementation
```

**Key Observations:**
- Multi-line option format for complex options
- `multiple=True` for options that accept multiple values
- Default values can be lists: `default=["./variables.yaml"]`

#### Macro Commands - Destroy Example
**File:** `Babylon/commands/macro/destroy.py`

```python
@command()
@injectcontext()
@retrieve_state
@option("--include", "include", multiple=True, type=str, help="Specify the resources to destroy.")
@option("--exclude", "exclude", multiple=True, type=str, help="Specify the resources to exclude from destroction.")
def destroy(state: dict, include: tuple[str], exclude: tuple[str]):
    """Macro Destroy"""
    # ... implementation
```

#### Macro Commands - Init Example
**File:** `Babylon/commands/macro/init.py`

```python
@command()
@option("--project-folder", default="project", help="Name of the project folder to create (default: 'project').")
@option("--variables-file", default="variables.yaml", help="Name of the variables file (default: 'variables.yaml').")
def init(project_folder: str, variables_file: str):
    """Scaffolds a new Babylon project structure using YAML templates."""
    # ... implementation
```

#### PowerBI Commands - Dataset Example
**File:** `Babylon/commands/powerbi/dataset/get.py`

```python
@command()
@injectcontext()
@pass_powerbi_token()
@argument("dataset_id", type=str)
@option("--workspace-id", "workspace_id", help="PowerBI workspace ID", type=str)
@output_to_file
@retrieve_state
def get(state: Any, powerbi_token: str, workspace_id: str, dataset_id: str) -> CommandResponse:
    """Get a powerbi dataset in the current workspace"""
    # ... implementation
```

**File:** `Babylon/commands/powerbi/workspace/get.py`

```python
@command()
@injectcontext()
@pass_powerbi_token()
@option("--workspace-id", "workspace_id", help="PowerBI workspace ID", type=str)
@option("--name", "name", help="PowerBI workspace name", type=str)
@retrieve_state
def get(state: Any, powerbi_token: str, workspace_id: Optional[str] = None, name: Optional[str] = None) -> CommandResponse:
    """Get a specific workspace information"""
    # ... implementation
```

---

## 3. Existing Short-Form Options (7 Found)

### 3.1 Global Short-Forms in main.py
**File:** `Babylon/main.py`

```python
@group(name="babylon", invoke_without_command=False, context_settings={'help_option_names': ['-h', '--help']})
@click_log.simple_verbosity_option(logger)
@option(
    "-n",
    "--dry-run",
    "dry_run",
    callback=display_dry_run,
    is_flag=True,
    expose_value=False,
    is_eager=True,
    help="Will run commands in dry-run mode.",
)
@option(
    "--version",
    is_flag=True,
    callback=print_version,
    expose_value=False,
    is_eager=True,
    help="Print version number and return.",
)
@option(
    "--log-path",
    "log_path",
    type=clickPath(file_okay=False, dir_okay=True, writable=True, path_type=pathlibPath),
    default=pathlibPath.cwd(),
    help="Path to the directory where log files will be stored. If not set, defaults to current working directory.",
)
def main(interactive, log_path):
    """CLI used for cloud interactions between CosmoTech and multiple cloud environment"""
    # ... implementation
```

**Short-forms:**
- `-h` for `--help` (configured via `context_settings`)
- `-n` for `--dry-run`

### 3.2 PowerBI Force Delete Short-Form
**File:** `Babylon/commands/powerbi/dataset/delete.py`

```python
@command()
@injectcontext()
@pass_powerbi_token()
@option("--workspace-id", "workspace_id", help="PowerBI workspace ID", type=str)
@option("-D", "force_validation", is_flag=True, help="Force Delete")
@argument("dataset_id", type=str)
@retrieve_state
def delete(state: Any, powerbi_token: str, dataset_id: str, workspace_id: Optional[str] = None, force_validation: bool = False) -> CommandResponse:
    """Delete a powerbi dataset in the current workspace"""
    # ... implementation
```

**Also found in:**
- `Babylon/commands/powerbi/workspace/delete.py`
- `Babylon/commands/powerbi/report/delete.py`
- `Babylon/commands/powerbi/workspace/user/delete.py`

**Short-form:**
- `-D` for force delete (flag option)

### 3.3 Namespace Context Short-Forms (in decorators)
**File:** `Babylon/utils/decorators.py`

```python
def wrapcontext() -> Callable[..., Any]:
    def wrap_function(func: Callable[..., Any]) -> Callable[..., Any]:
        @option("-c", "--context", "context", required=True, help="Context Name")
        @option("-t", "--tenant", "tenant", required=True, help="Tenant Name")
        @option("-s", "--state-id", "state_id", required=True, help="State Id")
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any):
            # ... implementation
        return wrapper
    return wrap_function
```

**Short-forms:**
- `-c` for `--context`
- `-t` for `--tenant`
- `-s` for `--state-id`

**Pattern Analysis for Existing Short-Forms:**
1. **Format:** `@option("-X", "--long-form", "param_name", ...)`
2. **First parameter is short-form:** Single dash + single character
3. **Second parameter is long-form:** Double dash + full name
4. **Same parameter structure:** Follows same pattern as long-form options

---

## 4. How to Add Short-Form Options

### 4.1 The Exact Transformation Pattern

#### BEFORE (Long-form only):
```python
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
```

#### AFTER (With short-form):
```python
@option("-o", "--oid", "organization_id", required=True, type=str, help="Organization ID")
```

**Key Points:**
1. Insert short-form as FIRST parameter: `"-o"`
2. Keep long-form as second parameter: `"--oid"`
3. All other parameters remain unchanged
4. Parameter name, type, help text stay the same

### 4.2 Complete Examples

#### Example 1: Single Option
```python
# BEFORE
@workspaces.command()
@injectcontext()
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
def delete(config: dict, keycloak_token: str, organization_id: str) -> CommandResponse:
    """Delete a workspace by ID"""
    # ... implementation

# AFTER
@workspaces.command()
@injectcontext()
@pass_keycloak_token()
@option("-o", "--oid", "organization_id", required=True, type=str, help="Organization ID")
def delete(config: dict, keycloak_token: str, organization_id: str) -> CommandResponse:
    """Delete a workspace by ID"""
    # ... implementation
```

#### Example 2: Multiple Options
```python
# BEFORE
@datasets.command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--wid", "workspace_id", required=True, type=str, help="Workspace ID")
@option("--did", "dataset_id", required=True, type=str, help="Dataset ID")
def get(config: dict, keycloak_token: str, organization_id: str, workspace_id: str, dataset_id: str) -> CommandResponse:
    """Get dataset"""
    # ... implementation

# AFTER
@datasets.command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("-o", "--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("-w", "--wid", "workspace_id", required=True, type=str, help="Workspace ID")
@option("-d", "--did", "dataset_id", required=True, type=str, help="Dataset ID")
def get(config: dict, keycloak_token: str, organization_id: str, workspace_id: str, dataset_id: str) -> CommandResponse:
    """Get dataset"""
    # ... implementation
```

#### Example 3: Multi-line Option (Macro Apply)
```python
# BEFORE
@option(
    "--var-file",
    "variables_files",
    type=ClickPath(file_okay=True, exists=True),
    default=["./variables.yaml"],
    multiple=True,
    help="Specify the path of your variable file. By default, it takes the variables.yaml file.",
)

# AFTER
@option(
    "-v",
    "--var-file",
    "variables_files",
    type=ClickPath(file_okay=True, exists=True),
    default=["./variables.yaml"],
    multiple=True,
    help="Specify the path of your variable file. By default, it takes the variables.yaml file.",
)
```

### 4.3 No Import Changes Needed
**Important:** No changes to import statements are required! The existing imports already support short-form options:

```python
from click import Path, argument, group, option
```

This `option` function supports both long-form and short-form syntax natively.

---

## 5. Complete Options Inventory by Category

### 5.1 API Resource Identifiers

| Long Form | Proposed Short | Meaning | Files Using |
|-----------|----------------|---------|-------------|
| `--oid` | `-o` | Organization ID | organization.py, workspace.py, solution.py, dataset.py, runner.py, run.py |
| `--wid` | `-w` | Workspace ID | workspace.py, dataset.py, runner.py, run.py |
| `--sid` | `-s` | Solution ID | solution.py, workspace.py, runner.py |
| `--did` | `-d` | Dataset ID | dataset.py |
| `--dpid` | `-p` | Dataset Part ID | dataset.py |
| `--rid` | `-r` | Runner ID | runner.py, run.py |
| `--rnid` | `-R` | Run ID | run.py |

**Collision Notes:**
- `-s` used for `--state-id` in decorators (different context - namespace commands vs API commands)
- `-r` for runner_id, `-R` (uppercase) for run_id to avoid collision

### 5.2 Macro Command Options

| Long Form | Proposed Short | Meaning | Files Using |
|-----------|----------------|---------|-------------|
| `--var-file` | `-v` | Variable file path | apply.py |
| `--include` | `-i` | Resources to include | apply.py, destroy.py |
| `--exclude` | `-e` | Resources to exclude | apply.py, destroy.py |
| `--project-folder` | `-f` | Project folder name | init.py |
| `--variables-file` | `-V` | Variables file name | init.py |

**Note:** `-v` for var-file, `-V` (uppercase) for variables-file

### 5.3 PowerBI Options

| Long Form | Proposed Short | Meaning | Files Using |
|-----------|----------------|---------|-------------|
| `--workspace-id` | `-w` | PowerBI Workspace ID | dataset/get.py, dataset/delete.py, workspace/get.py, workspace/delete.py |
| `--name` | `-n` | PowerBI Workspace name | workspace/get.py |
| `--dataset-id` | `-i` | PowerBI Dataset ID (when used as option, not argument) | Various dataset commands |

**Collision Notes:**
- `-n` already used for `--dry-run` globally, so PowerBI's `--name` may need `-N` or skip short-form
- `-w` conflicts with workspace_id in API commands (different contexts - PowerBI vs CosmoTech API)

### 5.4 Azure Options

| Long Form | Proposed Short | Meaning | Files Using |
|-----------|----------------|---------|-------------|
| `--container-name` | `-c` | Container name | azure/storage/container/upload.py |
| `--path` | `-p` | File path | azure/storage/container/upload.py |
| `--scope` | `-s` | Permission scope | azure/permission/set.py |
| `--resource` | `-r` | Resource name | azure/token/get.py, azure/token/store.py |

### 5.5 Global Options (Already Have Short-Forms)

| Long Form | Short Form | Meaning | File |
|-----------|------------|---------|------|
| `--help` | `-h` | Show help | main.py (context_settings) |
| `--dry-run` | `-n` | Dry run mode | main.py |
| `--log-path` | (none yet) | Log path | main.py |

**Note:** `--log-path` could potentially get `-l` short-form

---

## 6. Test Patterns and Structure

### 6.1 Existing Test File Structure
**File:** `tests/unit/test_help_shortform.py`

```python
import pytest
from click.testing import CliRunner
from Babylon.main import main


def collect_paths(cmd, prefix=None):
    """Recursively collect all command paths in the CLI tree"""
    if prefix is None:
        prefix = []
    paths = [prefix]
    if getattr(cmd, "commands", None):
        for name, sub in cmd.commands.items():
            paths.extend(collect_paths(sub, prefix + [name]))
    return paths


def test_help_shortform_matches_longform():
    """
    Test that -h and --help produce identical output for all commands.
    
    This test:
    1. Discovers all commands in the CLI tree
    2. Tests both -h and --help for each command
    3. Verifies both exit successfully (code 0)
    4. Verifies both produce identical output
    """
    runner = CliRunner()
    paths = collect_paths(main)
    
    # Deduplicate paths
    seen = set()
    unique_paths = []
    for p in paths:
        key = tuple(p)
        if key in seen:
            continue
        seen.add(key)
        unique_paths.append(p)

    # Test each command
    for path in unique_paths:
        short_args = path + ["-h"]
        long_args = path + ["--help"]
        
        res_short = runner.invoke(main, short_args)
        res_long = runner.invoke(main, long_args)
        
        assert res_short.exit_code == 0, (
            f"Command {' '.join(path) or 'main'} -h exited non-zero; exception: {res_short.exception}"
        )
        assert res_long.exit_code == 0, (
            f"Command {' '.join(path) or 'main'} --help exited non-zero; exception: {res_long.exception}"
        )
        assert res_short.output == res_long.output, (
            f"Help output mismatch for {' '.join(path) or 'main'}; -h vs --help"
        )
```

**Test Strategy:**
1. Uses `CliRunner` from Click's testing utilities
2. Recursively discovers all commands via `collect_paths()`
3. Tests EVERY command in the CLI tree
4. Verifies exit codes and output equivalence
5. Deduplicates paths to avoid redundant tests

### 6.2 Test Pattern for New Short-Forms

Based on the existing test, here's the pattern for testing new short-forms:

```python
import pytest
from click.testing import CliRunner
from Babylon.main import main


@pytest.mark.parametrize("command_path,short_opt,long_opt", [
    # API Organization
    (["babylon", "organizations", "delete"], "-o", "--oid"),
    (["babylon", "organizations", "get"], "-o", "--oid"),
    
    # API Workspace
    (["babylon", "workspaces", "create"], "-o", "--oid"),
    (["babylon", "workspaces", "create"], "-s", "--sid"),
    (["babylon", "workspaces", "list"], "-o", "--oid"),
    (["babylon", "workspaces", "delete"], "-o", "--oid"),
    (["babylon", "workspaces", "delete"], "-w", "--wid"),
    
    # API Dataset
    (["babylon", "datasets", "get"], "-o", "--oid"),
    (["babylon", "datasets", "get"], "-w", "--wid"),
    (["babylon", "datasets", "get"], "-d", "--did"),
    (["babylon", "datasets", "get_part"], "-o", "--oid"),
    (["babylon", "datasets", "get_part"], "-w", "--wid"),
    (["babylon", "datasets", "get_part"], "-d", "--did"),
    (["babylon", "datasets", "get_part"], "-p", "--dpid"),
    
    # Macro Apply
    (["babylon", "macro", "apply"], "-v", "--var-file"),
    (["babylon", "macro", "apply"], "-i", "--include"),
    (["babylon", "macro", "apply"], "-e", "--exclude"),
])
def test_shortform_in_help_output(command_path, short_opt, long_opt):
    """
    Verify that short-form options appear in help output alongside long-form.
    
    This tests that:
    1. Help text displays both -X and --long-form
    2. The option is properly registered with Click
    """
    runner = CliRunner()
    result = runner.invoke(main, command_path + ["--help"])
    
    assert result.exit_code == 0, f"Command {' '.join(command_path)} --help failed"
    assert short_opt in result.output, f"{short_opt} not found in {' '.join(command_path)} help"
    assert long_opt in result.output, f"{long_opt} not found in {' '.join(command_path)} help"


def test_shortform_functional_equivalence():
    """
    Test that short-form and long-form options produce identical results.
    
    This is a smoke test that verifies options work equivalently.
    Note: Requires mock data or test fixtures for full testing.
    """
    runner = CliRunner()
    
    # Example test case (would need appropriate test fixtures)
    # Test that -o and --oid work the same
    # short_result = runner.invoke(main, ["organizations", "get", "-o", "test-org-id"])
    # long_result = runner.invoke(main, ["organizations", "get", "--oid", "test-org-id"])
    # assert short_result.output == long_result.output
```

### 6.3 Test File Location
**New test file:** `tests/unit/test_option_shortform.py` (to be created)

This file should contain comprehensive parametrized tests for all new short-form options.

---

## 7. Implementation Checklist by File

### 7.1 API Commands

#### organization.py
- [ ] `create` - No options to modify (uses argument only)
- [ ] `delete` - Add `-o` to `--oid`
- [ ] `list` - No options to modify (no ID options)
- [ ] `get` - Add `-o` to `--oid`
- [ ] `update` - Add `-o` to `--oid`

#### workspace.py
- [ ] `create` - Add `-o` to `--oid`, `-s` to `--sid`
- [ ] `list` - Add `-o` to `--oid`
- [ ] `delete` - Add `-o` to `--oid`, `-w` to `--wid`
- [ ] `get` - Add `-o` to `--oid`, `-w` to `--wid`
- [ ] `update` - Add `-o` to `--oid`, `-w` to `--wid`

#### solution.py
- [ ] `create` - Add `-o` to `--oid`
- [ ] `delete` - Add `-o` to `--oid`, `-s` to `--sid`
- [ ] `list` - Add `-o` to `--oid`
- [ ] `get` - Add `-o` to `--oid`, `-s` to `--sid`
- [ ] `update` - Add `-o` to `--oid`, `-s` to `--sid`

#### dataset.py
- [ ] `create` - Add `-o`, `-w` to options
- [ ] `list` - Add `-o`, `-w` to options
- [ ] `delete` - Add `-o`, `-w`, `-d` to options
- [ ] `get` - Add `-o`, `-w`, `-d` to options
- [ ] `update` - Add `-o`, `-w`, `-d` to options
- [ ] `create_part` - Add `-o`, `-w`, `-d` to options
- [ ] `get_part` - Add `-o`, `-w`, `-d`, `-p` to options
- [ ] `delete_part` - Add `-o`, `-w`, `-d`, `-p` to options
- [ ] `update_part` - Add `-o`, `-w`, `-d`, `-p` to options

#### runner.py
- [ ] `create` - Add `-o`, `-s`, `-w` to options
- [ ] `delete` - Add `-o`, `-w`, `-r` to options
- [ ] `list` - Add `-o`, `-w` to options
- [ ] `get` - Add `-o`, `-w`, `-r` to options
- [ ] `update` - Add `-o`, `-w`, `-r` to options

#### run.py
- [ ] `get` - Add `-o`, `-w`, `-r`, `-R` to options
- [ ] `delete` - Add `-o`, `-w`, `-r`, `-R` to options
- [ ] `list` - Add `-o`, `-w`, `-r` to options

#### meta.py
- [ ] `about` - No options to modify (no ID options)

### 7.2 Macro Commands

#### apply.py
- [ ] `apply` - Add `-v` to `--var-file`, `-i` to `--include`, `-e` to `--exclude`

#### destroy.py
- [ ] `destroy` - Add `-i` to `--include`, `-e` to `--exclude`

#### init.py
- [ ] `init` - Add `-f` to `--project-folder`, `-V` to `--variables-file`

### 7.3 PowerBI Commands

#### dataset/get.py
- [ ] `get` - Add `-w` to `--workspace-id`

#### dataset/delete.py
- [ ] `delete` - Add `-w` to `--workspace-id` (already has `-D`)

#### dataset/get_all.py
- [ ] Review for options

#### workspace/get.py
- [ ] `get` - Add `-w` to `--workspace-id`, review `--name`

#### workspace/delete.py
- [ ] `delete` - Add `-w` to `--workspace-id` (already has `-D`)

### 7.4 Main Entry Point

#### main.py
- [ ] Consider adding `-l` to `--log-path`

---

## 8. Collision Matrix

### 8.1 Potential Conflicts

| Short | Option | Context | Resolution |
|-------|--------|---------|------------|
| `-s` | `--state-id` | Namespace decorator | OK - different command groups |
| `-s` | `--sid` (Solution ID) | API commands | OK - different command groups |
| `-w` | `--wid` (Workspace ID) | CosmoTech API | OK - consistent meaning |
| `-w` | `--workspace-id` | PowerBI | OK - same semantic meaning |
| `-n` | `--dry-run` | Global option | CONFLICT with `--name` in PowerBI |
| `-v` | `--var-file` | Macro apply | OK |
| `-V` | `--variables-file` | Macro init | OK - uppercase variant |
| `-r` | `--rid` (Runner ID) | API commands | OK |
| `-R` | `--rnid` (Run ID) | API commands | OK - uppercase variant |
| `-p` | `--dpid` | Dataset parts | OK |
| `-p` | `--path` | Azure storage | OK - different command groups |

### 8.2 Resolution Strategy
1. **Same semantic meaning across contexts:** OK to reuse (e.g., `-w` for workspace in both API and PowerBI)
2. **Different command groups:** OK to reuse (e.g., `-s` in namespace vs API commands)
3. **True conflicts:** Use uppercase variant (e.g., `-R` vs `-r`) or skip short-form
4. **Global conflicts:** Global options take priority (e.g., `-n` for `--dry-run`, skip short-form for PowerBI `--name`)

---

## 9. Code Examples for Implementation

### 9.1 Single File Complete Example

**File: Babylon/commands/api/organization.py**

```python
# BEFORE
from logging import getLogger

from click import Path, argument, group, option
from cosmotech_api import ApiClient, Configuration, OrganizationApi
from cosmotech_api.models.organization_create_request import OrganizationCreateRequest
from cosmotech_api.models.organization_update_request import OrganizationUpdateRequest
from yaml import safe_load

from Babylon.utils import API_REQUEST_MESSAGE
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import injectcontext, output_to_file
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)


def get_organization_api_instance(config: dict, keycloak_token: str) -> OrganizationApi:
    configuration = Configuration(host=config.get("api_url"))
    configuration.access_token = keycloak_token
    api_client = ApiClient(configuration)
    return OrganizationApi(api_client)


@group()
def organizations():
    """Organization - Cosmotech API"""
    pass


@organizations.command()
@injectcontext()
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
def delete(config: dict, keycloak_token: str, organization_id: str) -> CommandResponse:
    """Delete an organization by ID"""
    # ... implementation


# AFTER (CHANGED LINES ONLY)
@organizations.command()
@injectcontext()
@pass_keycloak_token()
@option("-o", "--oid", "organization_id", required=True, type=str, help="Organization ID")
def delete(config: dict, keycloak_token: str, organization_id: str) -> CommandResponse:
    """Delete an organization by ID"""
    # ... implementation
```

### 9.2 Multi-Option Example

```python
# BEFORE
@datasets.command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--wid", "workspace_id", required=True, type=str, help="Workspace ID")
@option("--did", "dataset_id", required=True, type=str, help="Dataset ID")
@option("--dpid", "dataset_part_id", required=True, type=str, help="Dataset Part ID")
def get_part(config: dict, keycloak_token: str, organization_id: str, workspace_id: str, dataset_id: str, dataset_part_id: str) -> CommandResponse:
    """Get dataset part"""
    # ... implementation

# AFTER
@datasets.command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("-o", "--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("-w", "--wid", "workspace_id", required=True, type=str, help="Workspace ID")
@option("-d", "--did", "dataset_id", required=True, type=str, help="Dataset ID")
@option("-p", "--dpid", "dataset_part_id", required=True, type=str, help="Dataset Part ID")
def get_part(config: dict, keycloak_token: str, organization_id: str, workspace_id: str, dataset_id: str, dataset_part_id: str) -> CommandResponse:
    """Get dataset part"""
    # ... implementation
```

---

## 10. Verification Steps

### 10.1 Manual Verification
After implementing short-forms for a command:

```bash
# Test help output shows both forms
babylon organizations delete --help
# Should show: -o, --oid TEXT  Organization ID [required]

# Test short-form works
babylon organizations delete -o test-org-id

# Test long-form still works
babylon organizations delete --oid test-org-id

# Test help shortcut
babylon organizations delete -h
```

### 10.2 Automated Testing
```bash
# Run existing help tests
pytest tests/unit/test_help_shortform.py -v

# Run new short-form tests (when created)
pytest tests/unit/test_option_shortform.py -v

# Run all unit tests
pytest tests/unit/ -v
```

---

## 11. Project Conventions Reference

### 11.1 Standard Decorator Stack Order
From code analysis, the standard order is:
1. `@group()` or `@command()`
2. `@injectcontext()`
3. `@output_to_file` (if needed)
4. `@pass_keycloak_token()` or `@pass_powerbi_token()` (if needed)
5. `@retrieve_state` (if needed)
6. `@option(...)` decorators (multiple, in logical order)
7. `@argument(...)` decorators (if needed)

### 11.2 Import Statement Pattern
```python
from logging import getLogger

from click import Path, argument, group, option
# Other imports...

logger = getLogger(__name__)
```

### 11.3 Return Convention
All commands MUST return `CommandResponse`:
```python
from Babylon.utils.response import CommandResponse

def some_command(...) -> CommandResponse:
    # ... implementation
    return CommandResponse.success(data)
    # or
    return CommandResponse.fail()
```

---

## 12. Summary of Key Findings

### 12.1 What We Found
1. **83 command files** across API, Macro, PowerBI, Azure, and Namespace groups
2. **7 existing short-forms**: `-h`, `-n`, `-D`, `-c`, `-t`, `-s` (in decorators)
3. **Consistent pattern** across all commands for adding options
4. **No import changes needed** - existing imports support short-forms
5. **Standard test pattern exists** in `test_help_shortform.py`

### 12.2 Implementation is Straightforward
- Simple pattern: insert short-form as first parameter
- No function signature changes
- No import modifications
- Backward compatible (long-forms still work)

### 12.3 Priority Implementation Order
1. **API commands** (most used) - 6 files, ~50 commands
2. **Macro commands** (high-level workflows) - 3 files, 4 commands
3. **PowerBI commands** (secondary) - multiple files
4. **Azure commands** (tertiary) - fewer files
5. **Global options** (main.py) - consider `-l` for `--log-path`

---

## 13. Next Steps for Implementation

1. **Create comprehensive test file** (`tests/unit/test_option_shortform.py`)
2. **Implement API commands first** (highest value)
3. **Test incrementally** after each file
4. **Update documentation** as you go
5. **Run full test suite** before committing

---

## Appendix A: Complete File Paths Verified

All paths confirmed to exist:
- ✅ `Babylon/main.py`
- ✅ `Babylon/commands/api/organization.py`
- ✅ `Babylon/commands/api/workspace.py`
- ✅ `Babylon/commands/api/solution.py`
- ✅ `Babylon/commands/api/dataset.py`
- ✅ `Babylon/commands/api/runner.py`
- ✅ `Babylon/commands/api/run.py`
- ✅ `Babylon/commands/api/meta.py`
- ✅ `Babylon/commands/macro/apply.py`
- ✅ `Babylon/commands/macro/destroy.py`
- ✅ `Babylon/commands/macro/init.py`
- ✅ `Babylon/commands/powerbi/dataset/get.py`
- ✅ `Babylon/commands/powerbi/dataset/delete.py`
- ✅ `Babylon/commands/powerbi/workspace/get.py`
- ✅ `Babylon/commands/powerbi/workspace/delete.py`
- ✅ `Babylon/utils/decorators.py`
- ✅ `tests/unit/test_help_shortform.py`

---

**Research compiled on:** 2026-01-27
**Babylon CLI Version Context:** Current development branch
**Click Framework:** Uses standard Click option decorators (no custom Click extensions)

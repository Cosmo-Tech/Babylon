# Short-Form Options Implementation (All Commands)

**Branch:** `feature/short-form-options-all`
**Description:** Add short-form alternatives (-X) for all CLI options where no conflicts exist

## Goal

Enable users to use short-form options (e.g., `-O` instead of `--oid`) across all Babylon CLI commands, improving CLI usability and reducing typing. Options with conflicts will be documented but not modified.

## Prerequisites

The `-h` help option has already been implemented. This plan covers all remaining options.

## Reserved Short-Form Letters (DO NOT USE)

These letters are already used globally by decorators or main.py:

| Letter | Used By | Option |
|--------|---------|--------|
| `-c` | `injectcontext`, `inject_required_context` | `--context` |
| `-f` | `output_to_file` | `--file` |
| `-h` | Global | `--help` |
| `-n` | main.py | `--dry-run` |
| `-o` | `output_to_file` | `--output` |
| `-s` | `injectcontext`, `inject_required_context` | `--state` |
| `-t` | `injectcontext`, `inject_required_context` | `--tenant` |
| `-D` | PowerBI delete commands | `--force-delete` (already has short-form) |

## Proposed Short-Form Mappings

| Long Option | Proposed Short | Status |
|-------------|---------------|--------|
| `--oid` (organization_id) | `-O` | ✅ Available |
| `--wid` (workspace_id) | `-W` | ✅ Available |
| `--sid` (solution_id) | `-S` | ✅ Available |
| `--did` (dataset_id) | `-d` | ✅ Available |
| `--rid` (runner_id) | `-r` | ✅ Available |
| `--rnid` (run_id) | `-R` | ✅ Available |
| `--dpid` (dataset_part_id) | `-p` | ✅ Available |
| `--namespace` | `-N` | ✅ Available |
| `--log-path` | `-l` | ✅ Available |
| `--workspace-id` (PowerBI) | `-w` | ✅ Available |
| `--email` | `-e` | ✅ Available |

## Conflicts Identified (NO CHANGES - Document Only)

| File | Option | Conflict Reason |
|------|--------|-----------------|
| `powerbi/report/download.py` | `--output/-o` | Already defined locally, would conflict with `output_to_file` decorator |
| `powerbi/report/download_all.py` | `--output/-o` | Already defined locally, would conflict with `output_to_file` decorator |
| `powerbi/dataset/parameters/get.py` | `--workspace-id` | Duplicated option definition (bug - needs separate fix) |

## ⚠️ IMPORTANT: Only Modify `@option` Decorators

This plan ONLY modifies `@option(...)` decorators to add short forms. 

**DO NOT modify:**
- `@argument(...)` decorators - arguments don't have short forms
- Function signatures
- Function bodies
- Import statements
- Any other code

**Pattern for changes:**
```python
# BEFORE:
@option("--long-name", "variable_name", ...)

# AFTER (add short form as first parameter):
@option("-X", "--long-name", "variable_name", ...)
```

---

## Implementation Steps

> ⚠️ **Workflow for Each Step:**
> 1. Make ONLY the specified `@option` changes (one line each)
> 2. Create/update test file with detailed tests for that step
> 3. Run tests: `source .venv/bin/activate && pytest tests/unit/test_option_shortform.py -v`
> 4. If tests pass → **STOP and wait for user to commit**
> 5. User commits, then proceed to next step

---

### Step 1: API Commands - Add Short-Form Options ✅ COMPLETED

**Status:** Already implemented in previous commits.

---

### Step 2: Macro Commands - Add Short-Form Options ✅ COMPLETED

**Status:** Already implemented in previous commits.

---

### Step 3: PowerBI Commands - Add Short-Form to `--workspace-id` Option

**What:** Add `-w` short form to all `--workspace-id` options in PowerBI commands.

**Files and EXACT line changes:**

Each change is a single-line modification to an `@option` decorator.

| File | Line | Before | After |
|------|------|--------|-------|
| `Babylon/commands/powerbi/dataset/get.py` | 18 | `@option("--workspace-id", ...)` | `@option("-w", "--workspace-id", ...)` |
| `Babylon/commands/powerbi/dataset/get_all.py` | 18 | `@option("--workspace-id", ...)` | `@option("-w", "--workspace-id", ...)` |
| `Babylon/commands/powerbi/dataset/take_over.py` | 17 | `@option("--workspace-id", ...)` | `@option("-w", "--workspace-id", ...)` |
| `Babylon/commands/powerbi/dataset/update_credentials.py` | 17 | `@option("--workspace-id", ...)` | `@option("-w", "--workspace-id", ...)` |
| `Babylon/commands/powerbi/dataset/parameters/update.py` | 25 | `@option("--workspace-id", ...)` | `@option("-w", "--workspace-id", ...)` |
| `Babylon/commands/powerbi/dataset/users/add.py` | 19 | `@option("--workspace-id", ...)` | `@option("-w", "--workspace-id", ...)` |
| `Babylon/commands/powerbi/report/delete.py` | 17 | `@option("--workspace-id", ...)` | `@option("-w", "--workspace-id", ...)` |
| `Babylon/commands/powerbi/report/get.py` | 24 | `@option("--workspace-id", ...)` | `@option("-w", "--workspace-id", ...)` |
| `Babylon/commands/powerbi/report/get_all.py` | 18 | `@option("--workspace-id", ...)` | `@option("-w", "--workspace-id", ...)` |
| `Babylon/commands/powerbi/report/upload.py` | 30 | `@option("--workspace-id", ...)` | `@option("-w", "--workspace-id", ...)` |
| `Babylon/commands/powerbi/report/pages.py` | 30 | `@option("--workspace-id", ...)` | `@option("-w", "--workspace-id", ...)` |
| `Babylon/commands/powerbi/report/download.py` | 26 | `@option("--workspace-id", ...)` | `@option("-w", "--workspace-id", ...)` |
| `Babylon/commands/powerbi/report/download_all.py` | 20 | `@option("--workspace-id", ...)` | `@option("-w", "--workspace-id", ...)` |
| `Babylon/commands/powerbi/workspace/delete.py` | 23 | `@option("--workspace-id", ...)` | `@option("-w", "--workspace-id", ...)` |
| `Babylon/commands/powerbi/workspace/get.py` | 22 | `@option("--workspace-id", ...)` | `@option("-w", "--workspace-id", ...)` |
| `Babylon/commands/powerbi/workspace/user/add.py` | 21 | `@option("--workspace-id", ...)` | `@option("-w", "--workspace-id", ...)` |
| `Babylon/commands/powerbi/workspace/user/delete.py` | 19 | `@option("--workspace-id", ...)` | `@option("-w", "--workspace-id", ...)` |

**SKIP** `Babylon/commands/powerbi/dataset/parameters/get.py` - has duplicated option definition (bug).

**Example change (dataset/get.py line 18):**
```python
# BEFORE:
@option("--workspace-id", "workspace_id", help="PowerBI workspace ID", type=str)

# AFTER:
@option("-w", "--workspace-id", "workspace_id", help="PowerBI workspace ID", type=str)
```

**Test code to add to `tests/unit/test_option_shortform.py`:**
```python
class TestPowerBIShortFormOptions:
    """Test short-form options for PowerBI commands."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    # Workspace ID (-w/--workspace-id)
    @pytest.mark.parametrize("command_path", [
        ["powerbi", "dataset", "get"],
        ["powerbi", "dataset", "get-all"],
        ["powerbi", "dataset", "take-over"],
        ["powerbi", "dataset", "update-credentials"],
        ["powerbi", "dataset", "parameters", "update"],
        ["powerbi", "dataset", "users", "add"],
        ["powerbi", "report", "delete"],
        ["powerbi", "report", "get"],
        ["powerbi", "report", "get-all"],
        ["powerbi", "report", "upload"],
        ["powerbi", "report", "pages"],
        ["powerbi", "report", "download"],
        ["powerbi", "report", "download-all"],
        ["powerbi", "workspace", "delete"],
        ["powerbi", "workspace", "get"],
        ["powerbi", "workspace", "user", "add"],
        ["powerbi", "workspace", "user", "delete"],
    ])
    def test_workspace_id_shortform_in_help(self, runner, command_path):
        """Verify -w/--workspace-id appears in help output."""
        result = runner.invoke(main, command_path + ["--help"])
        assert result.exit_code == 0
        if "--workspace-id" in result.output:
            assert "-w" in result.output, f"-w not found in {' '.join(command_path)} help"
```

**Execution:**
```bash
source .venv/bin/activate && pytest tests/unit/test_option_shortform.py::TestPowerBIShortFormOptions -v
```

**✅ On success:** Stop and wait for user commit before proceeding to Step 4.

---

### Step 4: PowerBI Dataset Users - Add Short-Form to `--email` Option

**What:** Add `-e` short form to `--email` option.

**Files and EXACT line changes:**

| File | Line | Before | After |
|------|------|--------|-------|
| `Babylon/commands/powerbi/dataset/users/add.py` | 20 | `@option("--email", ...)` | `@option("-e", "--email", ...)` |

**Example change:**
```python
# BEFORE:
@option("--email", "email", type=str, help="Email valid")

# AFTER:
@option("-e", "--email", "email", type=str, help="Email valid")
```

**Test code to add:**
```python
    # Email (-e/--email)
    @pytest.mark.parametrize("command_path", [
        ["powerbi", "dataset", "users", "add"],
    ])
    def test_email_shortform_in_help(self, runner, command_path):
        """Verify -e/--email appears in help output."""
        result = runner.invoke(main, command_path + ["--help"])
        assert result.exit_code == 0
        if "--email" in result.output:
            assert "-e" in result.output, f"-e not found in {' '.join(command_path)} help"
```

**Execution:**
```bash
source .venv/bin/activate && pytest tests/unit/test_option_shortform.py::TestPowerBIShortFormOptions -v
```

**✅ On success:** Stop and wait for user commit before proceeding to Step 5.

---

### Step 5: Azure Commands - Add Short-Form to `--email` Option

**What:** Add `-e` short form to `--email` option in Azure token commands.

**Files and EXACT line changes:**

| File | Line | Before | After |
|------|------|--------|-------|
| `Babylon/commands/azure/token/get.py` | 17 | `@option("--email", ...)` | `@option("-e", "--email", ...)` |
| `Babylon/commands/azure/token/store.py` | 17 | `@option("--email", ...)` | `@option("-e", "--email", ...)` |

**Example change:**
```python
# BEFORE:
@option("--email", "email", help="User email")

# AFTER:
@option("-e", "--email", "email", help="User email")
```

**Test code to add to `tests/unit/test_option_shortform.py`:**
```python
class TestAzureShortFormOptions:
    """Test short-form options for Azure commands."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    # Email (-e/--email)
    @pytest.mark.parametrize("command_path", [
        ["azure", "token", "get"],
        ["azure", "token", "store"],
    ])
    def test_email_shortform_in_help(self, runner, command_path):
        """Verify -e/--email appears in help output."""
        result = runner.invoke(main, command_path + ["--help"])
        assert result.exit_code == 0
        if "--email" in result.output:
            assert "-e" in result.output, f"-e not found in {' '.join(command_path)} help"
```

**Execution:**
```bash
source .venv/bin/activate && pytest tests/unit/test_option_shortform.py::TestAzureShortFormOptions -v
```

**✅ On success:** Stop and wait for user commit before proceeding to Step 6.

---

### Step 6: Main CLI - Add Short-Form for `--log-path`

**What:** Add `-l` short form for `--log-path` option in main.py.

**File and EXACT line change:**

| File | Line | Before | After |
|------|------|--------|-------|
| `Babylon/main.py` | ~98 | `@option("--log-path", ...)` | `@option("-l", "--log-path", ...)` |

**Example change:**
```python
# BEFORE:
@option(
    "--log-path",
    "log_path",
    type=clickPath(file_okay=False, dir_okay=True, writable=True, path_type=pathlibPath),
    default=pathlibPath.cwd(),
    help="Path to the directory where log files will be stored...",
)

# AFTER:
@option(
    "-l",
    "--log-path",
    "log_path",
    type=clickPath(file_okay=False, dir_okay=True, writable=True, path_type=pathlibPath),
    default=pathlibPath.cwd(),
    help="Path to the directory where log files will be stored...",
)
```

**Test code to add to `tests/unit/test_option_shortform.py`:**
```python
class TestMainCLIShortFormOptions:
    """Test short-form options for main CLI."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_log_path_shortform_in_help(self, runner):
        """Verify -l/--log-path appears in main help output."""
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "-l" in result.output, "-l not found in main help"
        assert "--log-path" in result.output, "--log-path not found in main help"
```

**Execution:**
```bash
source .venv/bin/activate && pytest tests/unit/test_option_shortform.py::TestMainCLIShortFormOptions -v
```

**✅ On success:** Stop and wait for user commit before proceeding to Step 7.

---

### Step 7: Documentation - Create Changes Report

**Files to create:**
- `plans/short-form-options/changes.md` (new file)

**What:** Document all options that received short forms and conflicts.

**Content:**
```markdown
# Short-Form Options Changes Report

## Implemented Short-Form Options

| Command Category | Long Option | Short Option | Files Modified |
|-----------------|-------------|--------------|----------------|
| API | `--oid` | `-O` | dataset.py, organization.py, run.py, runner.py, solution.py, workspace.py |
| API | `--wid` | `-W` | dataset.py, run.py, runner.py, workspace.py |
| API | `--sid` | `-S` | solution.py, workspace.py, runner.py |
| API | `--did` | `-d` | dataset.py |
| API | `--rid` | `-r` | run.py, runner.py |
| API | `--rnid` | `-R` | run.py |
| API | `--dpid` | `-p` | dataset.py |
| Macro | `--namespace` | `-N` | apply.py, deploy.py, destroy.py |
| PowerBI | `--workspace-id` | `-w` | 17 files |
| PowerBI | `--email` | `-e` | dataset/users/add.py |
| Azure | `--email` | `-e` | token/get.py, token/store.py |
| Main | `--log-path` | `-l` | main.py |

## Conflicts (Not Modified)

| File | Option | Conflict Reason |
|------|--------|-----------------|
| `powerbi/report/download.py` | `--output/-o` | Conflicts with `output_to_file` decorator |
| `powerbi/report/download_all.py` | `--output/-o` | Conflicts with `output_to_file` decorator |
| `powerbi/dataset/parameters/get.py` | `--workspace-id` | Duplicated option definition (separate bug) |

## Reserved Letters

Letters already in use globally: `-c`, `-f`, `-h`, `-n`, `-o`, `-s`, `-t`, `-D`
```

**Final test execution:**
```bash
source .venv/bin/activate && pytest tests/unit/test_option_shortform.py tests/unit/test_help_shortform.py -v
```

**✅ On success:** Stop and wait for user to make final commit.

---

## Summary of Remaining Steps

| Step | Category | Files to Modify | Options to Add Short Forms |
|------|----------|----------------|---------------------------|
| 3 | PowerBI Commands | 17 files | `--workspace-id` → `-w` |
| 4 | PowerBI Dataset Users | 1 file | `--email` → `-e` |
| 5 | Azure Commands | 2 files | `--email` → `-e` |
| 6 | Main CLI | 1 file | `--log-path` → `-l` |
| 7 | Documentation | 1 new file | Changes report |

---

## Critical Rules

1. **ONLY modify `@option` lines** - Never touch `@argument`, function signatures, or function bodies
2. **One parameter addition** - Add the short form as the FIRST parameter in the `@option` call
3. **Preserve everything else** - Keep all other parameters exactly as they are
4. **Test after each step** - Run the test suite before committing

**Correct pattern:**
```python
# Before:
@option("--long-name", "var_name", type=str, help="Description")

# After:
@option("-X", "--long-name", "var_name", type=str, help="Description")
#       ^^^^
#       Only this is added, everything else stays the same
```

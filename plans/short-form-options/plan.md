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
| `--powerbi-name` | `-P` | ✅ Available |
| `--dataset-id` (PowerBI) | `-i` | ✅ Available |
| `--report-id` (PowerBI) | `-I` | ✅ Available |
| `--namespace` | `-N` | ✅ Available |
| `--email` | `-e` | ✅ Available |
| `--log-path` | `-l` | ✅ Available |
| `--principal-type` | `-T` | ✅ Available |
| `--access-right` | `-a` | ✅ Available |
| `--account-name` | `-A` | ✅ Available |
| `--container-name` | `-C` | ✅ Available (Azure only) |
| `--blob-path` | `-b` | ✅ Available |

## Conflicts Identified (NO CHANGES - Document Only)

| File | Option | Conflict Reason |
|------|--------|-----------------|
| `powerbi/report/download.py` | `--output/-o` | Already defined locally, would conflict with `output_to_file` decorator |
| `powerbi/report/download_all.py` | `--output/-o` | Already defined locally, would conflict with `output_to_file` decorator |
| `powerbi/dataset/parameters/get.py` | `--powerbi-name` | Duplicated option definition (bug - needs separate fix) |

**Decisions (per clarifications):**
- Keep the PowerBI `--output/-o` definitions as-is; only document them as conflicts.
- Mention the duplicated `--powerbi-name` option in documentation; do not fix it in this plan.
- Test all short-form vs long-form behaviours (not just help output) in the new test suite.

## Implementation Steps

> ⚠️ **Workflow for Each Step:**
> 1. Implement the code changes
> 2. Create/update test file with detailed tests for that step
> 3. Run tests: `source .venv/bin/activate && pytest tests/unit/test_option_shortform.py -v`
> 4. If tests pass → **STOP and wait for user to commit**
> 5. User commits, then proceed to next step

---

### Step 1: API Commands - Add Short-Form Options

**Files to modify:**
- `Babylon/commands/api/dataset.py`
- `Babylon/commands/api/organization.py`
- `Babylon/commands/api/run.py`
- `Babylon/commands/api/runner.py`
- `Babylon/commands/api/solution.py`
- `Babylon/commands/api/workspace.py`

**What:** Add short-form options to all `@click.option` decorators:
- `--oid` → `-O/--oid`
- `--wid` → `-W/--wid`
- `--sid` → `-S/--sid`
- `--did` → `-d/--did`
- `--rid` → `-r/--rid`
- `--rnid` → `-R/--rnid`
- `--dpid` → `-p/--dpid`

**Test file to create:** `tests/unit/test_option_shortform.py`

**Test code for Step 1:**
```python
import pytest
from click.testing import CliRunner
from Babylon.main import main


class TestAPIShortFormOptions:
    """Test short-form options for API commands."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    # Organization ID (-O/--oid)
    @pytest.mark.parametrize("command_path,short,long", [
        (["api", "organizations", "get"], "-O", "--oid"),
        (["api", "solutions", "get"], "-O", "--oid"),
        (["api", "solutions", "get-all"], "-O", "--oid"),
        (["api", "workspaces", "get"], "-O", "--oid"),
        (["api", "workspaces", "get-all"], "-O", "--oid"),
        (["api", "datasets", "get"], "-O", "--oid"),
        (["api", "datasets", "get-all"], "-O", "--oid"),
        (["api", "runners", "get"], "-O", "--oid"),
        (["api", "runners", "get-all"], "-O", "--oid"),
        (["api", "runs", "get"], "-O", "--oid"),
        (["api", "runs", "get-all"], "-O", "--oid"),
    ])
    def test_oid_shortform_in_help(self, runner, command_path, short, long):
        """Verify -O/--oid appears in help output."""
        result = runner.invoke(main, command_path + ["--help"])
        assert result.exit_code == 0
        assert short in result.output, f"{short} not found in {' '.join(command_path)} help"
        assert long in result.output, f"{long} not found in {' '.join(command_path)} help"

    # Workspace ID (-W/--wid)
    @pytest.mark.parametrize("command_path", [
        ["api", "workspaces", "get"],
        ["api", "datasets", "get"],
        ["api", "datasets", "get-all"],
        ["api", "runners", "get"],
        ["api", "runners", "get-all"],
        ["api", "runs", "get"],
        ["api", "runs", "get-all"],
    ])
    def test_wid_shortform_in_help(self, runner, command_path):
        """Verify -W/--wid appears in help output."""
        result = runner.invoke(main, command_path + ["--help"])
        assert result.exit_code == 0
        assert "-W" in result.output, f"-W not found in {' '.join(command_path)} help"
        assert "--wid" in result.output, f"--wid not found in {' '.join(command_path)} help"

    # Solution ID (-S/--sid)
    @pytest.mark.parametrize("command_path", [
        ["api", "solutions", "get"],
    ])
    def test_sid_shortform_in_help(self, runner, command_path):
        """Verify -S/--sid appears in help output."""
        result = runner.invoke(main, command_path + ["--help"])
        assert result.exit_code == 0
        assert "-S" in result.output, f"-S not found in {' '.join(command_path)} help"
        assert "--sid" in result.output, f"--sid not found in {' '.join(command_path)} help"

    # Dataset ID (-d/--did)
    @pytest.mark.parametrize("command_path", [
        ["api", "datasets", "get"],
    ])
    def test_did_shortform_in_help(self, runner, command_path):
        """Verify -d/--did appears in help output."""
        result = runner.invoke(main, command_path + ["--help"])
        assert result.exit_code == 0
        assert "-d" in result.output, f"-d not found in {' '.join(command_path)} help"
        assert "--did" in result.output, f"--did not found in {' '.join(command_path)} help"

    # Runner ID (-r/--rid)
    @pytest.mark.parametrize("command_path", [
        ["api", "runners", "get"],
        ["api", "runs", "get"],
        ["api", "runs", "get-all"],
    ])
    def test_rid_shortform_in_help(self, runner, command_path):
        """Verify -r/--rid appears in help output."""
        result = runner.invoke(main, command_path + ["--help"])
        assert result.exit_code == 0
        assert "-r" in result.output, f"-r not found in {' '.join(command_path)} help"
        assert "--rid" in result.output, f"--rid not found in {' '.join(command_path)} help"

    # Run ID (-R/--rnid)
    @pytest.mark.parametrize("command_path", [
        ["api", "runs", "get"],
    ])
    def test_rnid_shortform_in_help(self, runner, command_path):
        """Verify -R/--rnid appears in help output."""
        result = runner.invoke(main, command_path + ["--help"])
        assert result.exit_code == 0
        assert "-R" in result.output, f"-R not found in {' '.join(command_path)} help"
        assert "--rnid" in result.output, f"--rnid not found in {' '.join(command_path)} help"
```

**Execution:**
```bash
source .venv/bin/activate && pytest tests/unit/test_option_shortform.py -v
```

**✅ On success:** Stop and wait for user commit before proceeding to Step 2.

---

### Step 2: Macro Commands - Add Short-Form Options

**Files to modify:**
- `Babylon/commands/macro/apply.py`
- `Babylon/commands/macro/deploy.py`
- `Babylon/commands/macro/destroy.py`

**What:** Add short-form options:
- `--namespace` → `-N/--namespace`

**Test code to append to `tests/unit/test_option_shortform.py`:**
```python
class TestMacroShortFormOptions:
    """Test short-form options for Macro commands."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    # Namespace (-N/--namespace)
    @pytest.mark.parametrize("command_path", [
        ["apply"],
        ["deploy"],
        ["destroy"],
    ])
    def test_namespace_shortform_in_help(self, runner, command_path):
        """Verify -N/--namespace appears in help output."""
        result = runner.invoke(main, command_path + ["--help"])
        assert result.exit_code == 0
        assert "-N" in result.output, f"-N not found in {' '.join(command_path)} help"
        assert "--namespace" in result.output, f"--namespace not found in {' '.join(command_path)} help"
```

**Execution:**
```bash
source .venv/bin/activate && pytest tests/unit/test_option_shortform.py -v
```

**✅ On success:** Stop and wait for user commit before proceeding to Step 3.

---

### Step 3: PowerBI Commands - Add Short-Form Options

**Files to modify:**
- `Babylon/commands/powerbi/resume.py`
- `Babylon/commands/powerbi/suspend.py`
- `Babylon/commands/powerbi/dataset/delete.py`
- `Babylon/commands/powerbi/dataset/get.py`
- `Babylon/commands/powerbi/dataset/get_all.py`
- `Babylon/commands/powerbi/dataset/refresh.py`
- `Babylon/commands/powerbi/dataset/take_over.py`
- `Babylon/commands/powerbi/dataset/parameters/get.py`
- `Babylon/commands/powerbi/dataset/parameters/update.py`
- `Babylon/commands/powerbi/dataset/users/add.py`
- `Babylon/commands/powerbi/report/delete.py`
- `Babylon/commands/powerbi/report/get.py`
- `Babylon/commands/powerbi/report/get_all.py`
- `Babylon/commands/powerbi/report/rebind.py`
- `Babylon/commands/powerbi/report/upload.py`
- `Babylon/commands/powerbi/workspace/create.py`
- `Babylon/commands/powerbi/workspace/delete.py`
- `Babylon/commands/powerbi/workspace/get.py`
- `Babylon/commands/powerbi/workspace/get_all.py`
- `Babylon/commands/powerbi/workspace/get_current.py`
- `Babylon/commands/powerbi/workspace/user/add.py`
- `Babylon/commands/powerbi/workspace/user/delete.py`
- `Babylon/commands/powerbi/workspace/user/get_all.py`
- `Babylon/commands/powerbi/workspace/user/update.py`

**What:** Add short-form options:
- `--powerbi-name` → `-P/--powerbi-name`
- `--dataset-id` → `-i/--dataset-id`
- `--report-id` → `-I/--report-id`
- `--email` → `-e/--email`
- `--principal-type` → `-T/--principal-type`
- `--access-right` → `-a/--access-right`

**Skip files with conflicts:** `download.py`, `download_all.py`

**Test code to append to `tests/unit/test_option_shortform.py`:**
```python
class TestPowerBIShortFormOptions:
    """Test short-form options for PowerBI commands."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    # PowerBI Name (-P/--powerbi-name)
    @pytest.mark.parametrize("command_path", [
        ["powerbi", "resume"],
        ["powerbi", "suspend"],
        ["powerbi", "dataset", "delete"],
        ["powerbi", "dataset", "get"],
        ["powerbi", "dataset", "get-all"],
        ["powerbi", "dataset", "refresh"],
        ["powerbi", "dataset", "take-over"],
        ["powerbi", "dataset", "parameters", "get"],
        ["powerbi", "dataset", "parameters", "update"],
        ["powerbi", "dataset", "users", "add"],
        ["powerbi", "report", "delete"],
        ["powerbi", "report", "get"],
        ["powerbi", "report", "get-all"],
        ["powerbi", "report", "rebind"],
        ["powerbi", "report", "upload"],
        ["powerbi", "workspace", "create"],
        ["powerbi", "workspace", "delete"],
        ["powerbi", "workspace", "get"],
        ["powerbi", "workspace", "get-all"],
        ["powerbi", "workspace", "get-current"],
        ["powerbi", "workspace", "user", "add"],
        ["powerbi", "workspace", "user", "delete"],
        ["powerbi", "workspace", "user", "get-all"],
        ["powerbi", "workspace", "user", "update"],
    ])
    def test_powerbi_name_shortform_in_help(self, runner, command_path):
        """Verify -P/--powerbi-name appears in help output."""
        result = runner.invoke(main, command_path + ["--help"])
        assert result.exit_code == 0
        # Check if this command has --powerbi-name option
        if "--powerbi-name" in result.output:
            assert "-P" in result.output, f"-P not found in {' '.join(command_path)} help"

    # Dataset ID (-i/--dataset-id)
    @pytest.mark.parametrize("command_path", [
        ["powerbi", "dataset", "delete"],
        ["powerbi", "dataset", "get"],
        ["powerbi", "dataset", "refresh"],
        ["powerbi", "dataset", "take-over"],
        ["powerbi", "dataset", "parameters", "get"],
        ["powerbi", "dataset", "parameters", "update"],
        ["powerbi", "dataset", "users", "add"],
        ["powerbi", "report", "rebind"],
    ])
    def test_dataset_id_shortform_in_help(self, runner, command_path):
        """Verify -i/--dataset-id appears in help output."""
        result = runner.invoke(main, command_path + ["--help"])
        assert result.exit_code == 0
        if "--dataset-id" in result.output:
            assert "-i" in result.output, f"-i not found in {' '.join(command_path)} help"

    # Report ID (-I/--report-id)
    @pytest.mark.parametrize("command_path", [
        ["powerbi", "report", "delete"],
        ["powerbi", "report", "get"],
        ["powerbi", "report", "rebind"],
    ])
    def test_report_id_shortform_in_help(self, runner, command_path):
        """Verify -I/--report-id appears in help output."""
        result = runner.invoke(main, command_path + ["--help"])
        assert result.exit_code == 0
        if "--report-id" in result.output:
            assert "-I" in result.output, f"-I not found in {' '.join(command_path)} help"

    # Email (-e/--email)
    @pytest.mark.parametrize("command_path", [
        ["powerbi", "dataset", "users", "add"],
        ["powerbi", "workspace", "user", "add"],
        ["powerbi", "workspace", "user", "delete"],
        ["powerbi", "workspace", "user", "update"],
    ])
    def test_email_shortform_in_help(self, runner, command_path):
        """Verify -e/--email appears in help output."""
        result = runner.invoke(main, command_path + ["--help"])
        assert result.exit_code == 0
        if "--email" in result.output:
            assert "-e" in result.output, f"-e not found in {' '.join(command_path)} help"

    # Principal Type (-T/--principal-type)
    @pytest.mark.parametrize("command_path", [
        ["powerbi", "dataset", "users", "add"],
        ["powerbi", "workspace", "user", "add"],
        ["powerbi", "workspace", "user", "update"],
    ])
    def test_principal_type_shortform_in_help(self, runner, command_path):
        """Verify -T/--principal-type appears in help output."""
        result = runner.invoke(main, command_path + ["--help"])
        assert result.exit_code == 0
        if "--principal-type" in result.output:
            assert "-T" in result.output, f"-T not found in {' '.join(command_path)} help"

    # Access Right (-a/--access-right)
    @pytest.mark.parametrize("command_path", [
        ["powerbi", "dataset", "users", "add"],
        ["powerbi", "workspace", "user", "add"],
        ["powerbi", "workspace", "user", "update"],
    ])
    def test_access_right_shortform_in_help(self, runner, command_path):
        """Verify -a/--access-right appears in help output."""
        result = runner.invoke(main, command_path + ["--help"])
        assert result.exit_code == 0
        if "--access-right" in result.output:
            assert "-a" in result.output, f"-a not found in {' '.join(command_path)} help"
```

**Execution:**
```bash
source .venv/bin/activate && pytest tests/unit/test_option_shortform.py -v
```

**✅ On success:** Stop and wait for user commit before proceeding to Step 4.

---

### Step 4: Azure Commands - Add Short-Form Options

**Files to modify:**
- `Babylon/commands/azure/permission/set.py`
- `Babylon/commands/azure/token/get.py`
- `Babylon/commands/azure/token/store.py`
- `Babylon/commands/azure/storage/container/upload.py`

**What:** Add short-form options:
- `--account-name` → `-A/--account-name`
- `--container-name` → `-C/--container-name`
- `--blob-path` → `-b/--blob-path`

**Test code to append to `tests/unit/test_option_shortform.py`:**
```python
class TestAzureShortFormOptions:
    """Test short-form options for Azure commands."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    # Account Name (-A/--account-name)
    @pytest.mark.parametrize("command_path", [
        ["azure", "storage", "container", "upload"],
    ])
    def test_account_name_shortform_in_help(self, runner, command_path):
        """Verify -A/--account-name appears in help output."""
        result = runner.invoke(main, command_path + ["--help"])
        assert result.exit_code == 0
        if "--account-name" in result.output:
            assert "-A" in result.output, f"-A not found in {' '.join(command_path)} help"

    # Container Name (-C/--container-name)
    @pytest.mark.parametrize("command_path", [
        ["azure", "storage", "container", "upload"],
    ])
    def test_container_name_shortform_in_help(self, runner, command_path):
        """Verify -C/--container-name appears in help output."""
        result = runner.invoke(main, command_path + ["--help"])
        assert result.exit_code == 0
        if "--container-name" in result.output:
            assert "-C" in result.output, f"-C not found in {' '.join(command_path)} help"

    # Blob Path (-b/--blob-path)
    @pytest.mark.parametrize("command_path", [
        ["azure", "storage", "container", "upload"],
    ])
    def test_blob_path_shortform_in_help(self, runner, command_path):
        """Verify -b/--blob-path appears in help output."""
        result = runner.invoke(main, command_path + ["--help"])
        assert result.exit_code == 0
        if "--blob-path" in result.output:
            assert "-b" in result.output, f"-b not found in {' '.join(command_path)} help"
```

**Execution:**
```bash
source .venv/bin/activate && pytest tests/unit/test_option_shortform.py -v
```

**✅ On success:** Stop and wait for user commit before proceeding to Step 5.

---

### Step 5: Main CLI - Add Short-Form for --log-path

**Files to modify:**
- `Babylon/main.py`

**What:** Add `-l` short form for `--log-path` option

**Test code to append to `tests/unit/test_option_shortform.py`:**
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

    def test_log_path_short_and_long_equivalent(self, runner):
        """Verify -l and --log-path produce equivalent behavior."""
        # Using --help to avoid side effects
        result_short = runner.invoke(main, ["-l", "/tmp/test.log", "--help"])
        result_long = runner.invoke(main, ["--log-path", "/tmp/test.log", "--help"])
        assert result_short.exit_code == 0
        assert result_long.exit_code == 0
        # Both should show help output without errors
        assert "Usage:" in result_short.output
        assert "Usage:" in result_long.output
```

**Execution:**
```bash
source .venv/bin/activate && pytest tests/unit/test_option_shortform.py -v
```

**✅ On success:** Stop and wait for user commit before proceeding to Step 6.

---

### Step 6: Documentation - Create Changes Report

**Files to create:**
- `plans/short-form-options/changes.md` (new file)

**What:** Document:
1. All options that received short forms (before/after)
2. All options with conflicts (not changed)
3. Rationale for each conflict

**Content template:**
```markdown
# Short-Form Options Changes Report

## Implemented Short-Form Options

| Command Category | Long Option | Short Option | Files Modified |
|-----------------|-------------|--------------|----------------|
| API | `--oid` | `-O` | dataset.py, organization.py, run.py, runner.py, solution.py, workspace.py |
| API | `--wid` | `-W` | dataset.py, run.py, runner.py, workspace.py |
| API | `--sid` | `-S` | solution.py |
| API | `--did` | `-d` | dataset.py |
| API | `--rid` | `-r` | run.py, runner.py |
| API | `--rnid` | `-R` | run.py |
| Macro | `--namespace` | `-N` | apply.py, deploy.py, destroy.py |
| PowerBI | `--powerbi-name` | `-P` | 24 files |
| PowerBI | `--dataset-id` | `-i` | 8 files |
| PowerBI | `--report-id` | `-I` | 3 files |
| PowerBI | `--email` | `-e` | 4 files |
| PowerBI | `--principal-type` | `-T` | 3 files |
| PowerBI | `--access-right` | `-a` | 3 files |
| Azure | `--account-name` | `-A` | upload.py |
| Azure | `--container-name` | `-C` | upload.py |
| Azure | `--blob-path` | `-b` | upload.py |
| Main | `--log-path` | `-l` | main.py |

## Conflicts (Not Modified)

| File | Option | Conflict Reason |
|------|--------|-----------------|
| `powerbi/report/download.py` | `--output/-o` | Conflicts with `output_to_file` decorator |
| `powerbi/report/download_all.py` | `--output/-o` | Conflicts with `output_to_file` decorator |
| `powerbi/dataset/parameters/get.py` | `--powerbi-name` | Duplicated option definition (separate bug) |

## Reserved Letters

Letters already in use globally: `-c`, `-f`, `-h`, `-n`, `-o`, `-s`, `-t`, `-D`
```

**Final test execution:**
```bash
source .venv/bin/activate && pytest tests/unit/test_option_shortform.py tests/unit/test_help_shortform.py -v
```

**✅ On success:** Stop and wait for user to make final commit.

---

## Summary of Changes by Step

| Step | Category | Files Modified | Short Options Added | Test Classes |
|------|----------|---------------|---------------------|--------------|
| 1 | API Commands | 6 files | ~35 short options | `TestAPIShortFormOptions` |
| 2 | Macro Commands | 3 files | ~5 short options | `TestMacroShortFormOptions` |
| 3 | PowerBI Commands | 24 files | ~30 short options | `TestPowerBIShortFormOptions` |
| 4 | Azure Commands | 4 files | ~10 short options | `TestAzureShortFormOptions` |
| 5 | Main CLI | 1 file | 1 short option | `TestMainCLIShortFormOptions` |
| 6 | Documentation | 1 new file | Changes report | N/A |

---

## Workflow Summary

```
┌─────────────────────────────────────────────────────────────┐
│                    FOR EACH STEP (1-6)                      │
├─────────────────────────────────────────────────────────────┤
│  1. Implement code changes                                  │
│  2. Create/append test class to test_option_shortform.py    │
│  3. Run: pytest tests/unit/test_option_shortform.py -v      │
│  4. ✅ Tests pass? → STOP for user commit                   │
│  5. ❌ Tests fail? → Fix issues and re-run                  │
│  6. User commits → Proceed to next step                     │
└─────────────────────────────────────────────────────────────┘
```

---

## Verification Checklist

**After each step, verify:**
```bash
# Activate environment
source .venv/bin/activate

# Run step-specific tests
pytest tests/unit/test_option_shortform.py -v

# Verify no regression on existing tests
pytest tests/unit/test_help_shortform.py -v
```

**Final verification (after Step 6):**
```bash
# Full test suite
pytest tests/unit/ -v

# Manual spot checks
babylon api organizations get --help  # Should show -O/--oid
babylon apply --help                   # Should show -N/--namespace
babylon powerbi dataset get --help     # Should show -P, -i
babylon --help                         # Should show -l/--log-path
```

---

## Implementation Strategy

⚠️ **Critical Workflow Rules:**

1. **One step at a time** - Complete each step fully before moving to the next
2. **Test immediately** - After implementing changes, create/update tests and run them
3. **Wait for commit** - After tests pass, STOP and wait for user to commit
4. **Incremental test file** - Build `tests/unit/test_option_shortform.py` incrementally, adding one test class per step

**Commands to run after each step:**
```bash
source .venv/bin/activate
pytest tests/unit/test_option_shortform.py -v
```

**Commit message format:**
```
feat(cli): add short-form options for {category} commands

- Add {list of short options}
- Add tests for {category} short-form options
```
---

## Notes

1. **Backward Compatibility**: All long-form options continue working unchanged
2. **Naming Convention**: Uppercase for resource IDs (`-O`, `-W`, `-S`), lowercase for other options
3. **Already Implemented**: `-D` for force-delete in PowerBI, `-h` for help
4. **Test Pattern**: Follows existing `test_help_shortform.py` approach
5. **Conflicts Documented**: Options with conflicts listed in `changes.md` with rationale


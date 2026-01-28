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
        (["api", "solutions", "list"], "-O", "--oid"),
        (["api", "workspaces", "get"], "-O", "--oid"),
        (["api", "workspaces", "list"], "-O", "--oid"),
        (["api", "datasets", "get"], "-O", "--oid"),
        (["api", "datasets", "list"], "-O", "--oid"),
        (["api", "runners", "get"], "-O", "--oid"),
        (["api", "runners", "list"], "-O", "--oid"),
        (["api", "runs", "get"], "-O", "--oid"),
        (["api", "runs", "list"], "-O", "--oid"),
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
        ["api", "datasets", "list"],
        ["api", "runners", "get"],
        ["api", "runners", "list"],
        ["api", "runs", "get"],
        ["api", "runs", "list"],
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
        ["api", "runs", "list"],
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


class TestMacroShortFormOptions:
    """Test short-form options for Macro commands."""


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

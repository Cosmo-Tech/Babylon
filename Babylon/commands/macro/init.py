import subprocess
from logging import getLogger
from pathlib import Path
from shutil import copy

from click import Choice, argument, command, echo, option, style

from Babylon.utils.environment import Environment

logger = getLogger(__name__)
env = Environment()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_TF_WEBAPP_DIR = "terraform-webapp"
_TF_WEBAPP_REPO_URL = "https://github.com/Cosmo-Tech/terraform-webapp.git"
_TF_WEBAPP_DEFAULT_VERSION = "1.1.0"
_CORE_VARIABLES_TEMPLATE = "variables.core.yaml"
_WORKSPACE_VARIABLES_TEMPLATE = "variables.workspace.yaml"

# YAML files that live in core/ (shared across all workspaces)
_CORE_YAML_FILES = [
    "Organization.yaml",
    "Solution.yaml",
]

# YAML files that live in each workspace's deploy/ directory
_WORKSPACE_YAML_FILES = [
    "Workspace.yaml",
]

# Dashboard sub-directories to scaffold under <workspace>/deploy/dashboard/
_DASHBOARD_PROVIDERS = ["superset", "powerbi"]
_SUPPORTED_CLOUD_PROVIDERS = {"azure", "kob"}


# ---------------------------------------------------------------------------
# Private helpers — templates
# ---------------------------------------------------------------------------


def _get_provider_template(cloud_provider: str, filename: str) -> Path:
    """Return the template path for *filename* scoped to *cloud_provider*,
    falling back to the shared yaml directory when no provider variant exists."""
    provider = cloud_provider.lower()
    if provider in _SUPPORTED_CLOUD_PROVIDERS:
        candidate = env.original_template_path / "yaml" / provider / filename
        if candidate.exists():
            return candidate
    return env.original_template_path / "yaml" / filename


# ---------------------------------------------------------------------------
# Private helpers — terraform-webapp
# ---------------------------------------------------------------------------


def _clone_webapp(tf_webapp_path: Path, version: str) -> None:
    """Clone the Terraform WebApp repository at *version* into *tf_webapp_path*."""
    logger.info(f"  [dim]→ Cloning Terraform WebApp module (version [cyan]{version}[/cyan])...[/dim]")
    try:
        subprocess.run(
            ["git", "clone", "-q", _TF_WEBAPP_REPO_URL, str(tf_webapp_path)],
            check=True,
            stdout=subprocess.DEVNULL,
        )
        subprocess.run(
            ["git", "-C", str(tf_webapp_path), "checkout", "-q", version],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if tf_webapp_path.exists():
            logger.info(f"  [green]✔[/green] Terraform WebApp module cloned at version [cyan]{version}[/cyan]")
        else:
            logger.error("  [bold red]✘[/bold red] Terraform WebApp module was not created after cloning")
    except subprocess.CalledProcessError as exc:
        logger.error(f"  [bold red]✘[/bold red] Failed to clone Terraform repo: {exc}")


def _ensure_webapp(tf_webapp_path: Path, version: str) -> None:
    """Ensure *tf_webapp_path* exists at the requested *version*.

    - If the directory does not exist, clone it and check out *version*.
    - If it already exists, switch to *version* (no-op if already on it).
    """
    if tf_webapp_path.exists():
        logger.info("  [green]✔[/green] Webapp directory [cyan]terraform-webapp[/cyan] already exists.")
        try:
            subprocess.run(
                ["git", "-C", str(tf_webapp_path), "checkout", "-q", version],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            logger.info(f"  [green]✔[/green] Terraform WebApp version set to [cyan]{version}[/cyan]")
        except subprocess.CalledProcessError as exc:
            logger.error(f"  [bold red]✘[/bold red] Could not switch terraform-webapp to version {version}: {exc}")
    else:
        logger.warning("  [bold yellow]![/bold yellow] Webapp directory not found")
        _clone_webapp(tf_webapp_path, version)


# ---------------------------------------------------------------------------
# Private helpers — core layer
# ---------------------------------------------------------------------------


def _scaffold_core(core_path: Path, cloud_provider: str) -> None:
    """Create core/ and populate it with shared resource YAML files and
    a variables.core.yaml template."""
    core_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"  [dim]→ Created directory: [cyan]{core_path.name}/[/cyan][/dim]")

    # Shared resource manifests (Organization + Solution)
    for filename in _CORE_YAML_FILES:
        src = env.original_template_path / "yaml" / filename
        if src.exists():
            copy(src, core_path / filename)
            logger.info(f"  [green]✔[/green] Generated [white]core/{filename}[/white]")
        else:
            logger.warning(f"  [yellow]⚠[/yellow] Template not found for [white]{filename}[/white], skipping")

    # Webapp.yaml (cloud-provider-specific) lives in core/ shared across all workspaces
    webapp_src = _get_provider_template(cloud_provider, "Webapp.yaml")
    if webapp_src.exists():
        copy(webapp_src, core_path / "Webapp.yaml")
        logger.info(f"  [green]✔[/green] Generated [white]core/Webapp.yaml[/white] (provider: {cloud_provider})")
    else:
        logger.warning(f"  [yellow]⚠[/yellow] Webapp.yaml template not found for provider [cyan]{cloud_provider}[/cyan]")

    # Global variables shared by all workspaces → core/variables.core.yaml
    vars_src = _get_provider_template(cloud_provider, _CORE_VARIABLES_TEMPLATE)
    vars_dst = core_path / "variables.core.yaml"
    if not vars_dst.exists():
        if vars_src.exists():
            copy(vars_src, vars_dst)
            logger.info(f"  [green]✔[/green] Generated [white]core/variables.core.yaml[/white] (provider: {cloud_provider})")
        else:
            logger.warning("  [yellow]⚠[/yellow] variables.core.yaml template not found, skipping core variables")
    else:
        logger.info("  [green]✔[/green] [white]core/variables.core.yaml[/white] already exists, skipping")


# ---------------------------------------------------------------------------
# Private helpers — workspace layer
# ---------------------------------------------------------------------------


def _scaffold_workspace(workspaces_path: Path, workspace_name: str, cloud_provider: str) -> None:
    """Create workspaces/<workspace_name>/ with its deploy/ sub-directory,
    dashboard directories, and a workspace-scoped variables.yaml.

    Skips silently if the workspace already exists (idempotent).
    """
    ws_path = workspaces_path / workspace_name
    deploy_path = ws_path / "deploy"

    # Skip entirely if already scaffolded
    if ws_path.exists():
        logger.info(f"  [green]✔[/green] Workspace [cyan]{workspace_name}[/cyan] already exists, skipping")
        return

    for d in [ws_path, deploy_path]:
        d.mkdir(parents=True, exist_ok=True)
        logger.info(f"  [dim]→ Created directory: [cyan]{d.relative_to(workspaces_path.parent)}/[/cyan][/dim]")

    # Workspace.yaml → deploy/
    for filename in _WORKSPACE_YAML_FILES:
        src = env.original_template_path / "yaml" / filename
        if src.exists():
            copy(src, deploy_path / filename)
            logger.info(f"  [green]✔[/green] Generated [white]workspaces/{workspace_name}/deploy/{filename}[/white]")
        else:
            logger.warning(f"  [yellow]⚠[/yellow] Template not found for [white]{filename}[/white], skipping")

    # deploy/dashboard/<provider>/
    for provider in _DASHBOARD_PROVIDERS:
        provider_path = deploy_path / "dashboard" / provider
        provider_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"  [dim]→ Created directory: [cyan]workspaces/{workspace_name}/deploy/dashboard/{provider}/[/cyan][/dim]")

    # Workspace-scoped variables file named to match the workspace index (e.g. variables-1.yaml)
    ws_index = workspace_name.split("-")[-1]  # "workspace-1" → "1"
    vars_filename = f"variables-{ws_index}.yaml"
    vars_src = _get_provider_template(cloud_provider, _WORKSPACE_VARIABLES_TEMPLATE)
    vars_dst = ws_path / vars_filename
    if vars_src.exists():
        copy(vars_src, vars_dst)
        logger.info(f"  [green]✔[/green] Generated [white]workspaces/{workspace_name}/{vars_filename}[/white]")
    else:
        logger.warning(f"  [yellow]⚠[/yellow] variables.workspace.yaml template not found for workspace [cyan]{workspace_name}[/cyan]")


# ---------------------------------------------------------------------------
# Private helpers — full scaffold orchestration
# ---------------------------------------------------------------------------


def _scaffold_project(
    root_path: Path,
    project_dir: str,
    num_workspaces: int,
    cloud_provider: str,
    tf_webapp_version: str,
) -> None:
    """Orchestrate the full two-tier project scaffold.

    Generated layout:
      ./
      ├── <project_dir>/
      │   ├── core/
      │   └── workspaces/
      │       ├── workspace-1/
      │       └── workspace-N/
      └── terraform-webapp/
    """
    project_path = root_path / project_dir
    total_steps = 2 + num_workspaces  # core + N workspaces + terraform-webapp
    step = 1

    try:
        echo(style("\n📁 Scaffolding project structure...", fg="cyan", bold=True))

        # Project root folder
        project_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"  [dim]→ Created directory: [cyan]{project_dir}/[/cyan][/dim]")

        # Core layer (always step 1)
        echo(style(f"\n  [{step}/{total_steps}] Core layer", fg="white", bold=True))
        _scaffold_core(project_path / "core", cloud_provider)
        step += 1

        # Workspace layers
        workspaces_path = project_path / "workspaces"
        workspace_names = [f"workspace-{i}" for i in range(1, num_workspaces + 1)]
        for ws_name in workspace_names:
            echo(style(f"\n  [{step}/{total_steps}] Workspace layer — {ws_name}", fg="white", bold=True))
            _scaffold_workspace(workspaces_path, ws_name, cloud_provider)
            step += 1

        # Terraform WebApp cloned at the same level as project_dir
        echo(style(f"\n  [{step}/{total_steps}] Terraform WebApp module", fg="white", bold=True))
        _ensure_webapp(root_path / _TF_WEBAPP_DIR, tf_webapp_version)

        _print_success_summary(project_path, project_dir, workspace_names)

    except OSError as exc:
        logger.error("  [bold red]✘[/bold red] An error occurred while scaffolding see babylon logs for details")
        logger.debug(f"  Error details: {exc}", exc_info=True)


def _print_success_summary(project_path: Path, project_dir: str, workspace_names: list[str]) -> None:
    echo(style("\n🚀 Project successfully initialized!", fg="green", bold=True))
    echo(style(f"   Path: {project_path}", fg="white", dim=True))
    echo(style("\n▶", fg="green", bold=True), nl=False)
    echo(style(" Next steps:", fg="white", bold=True))
    echo(style(f"  1. Edit  {project_dir}/core/variables.core.yaml", fg="cyan"))
    for ws_name in workspace_names:
        ws_index = ws_name.split("-")[-1]
        echo(style(f"  2. Edit  {project_dir}/workspaces/{ws_name}/variables-{ws_index}.yaml", fg="cyan"))

# ---------------------------------------------------------------------------
# CLI command
# ---------------------------------------------------------------------------


@command()
@option(
    "--project-dir",
    "project_dir",
    default="project",
    show_default=True,
    help="Name of the root project folder to create (default: 'project').",
)
@option(
    "--workspaces",
    "-w",
    "num_workspaces",
    default=1,
    show_default=True,
    type=int,
    help="Number of workspaces to scaffold (workspace-1 … workspace-N).",
)
@option(
    "--tf-webapp-version",
    "tf_webapp_version",
    default=_TF_WEBAPP_DEFAULT_VERSION,
    show_default=True,
    help=f"Version (tag) of the terraform-webapp module to clone/checkout. Default: {_TF_WEBAPP_DEFAULT_VERSION}.",
)
@argument("cloud_provider", type=Choice(["azure", "kob"], case_sensitive=False))
def init(project_dir: str, num_workspaces: int, tf_webapp_version: str, cloud_provider: str):
    """Scaffold a new multi-workspace Babylon project in the current directory.

    Creates the two-tier structure inside a project folder:

    \b
      <project-dir>/
      ├── core/                      shared Organization, Solution, Webapp + global variables
      ├── workspaces/workspace-1/    isolated workspace resources + workspace variables
      ├── workspaces/workspace-N/    (one directory per --workspaces count)
      └── terraform-webapp/          Terraform WebApp module (cloned from GitHub)

    \b
    Examples:

    \b
      babylon macro init azure                          # project/ with 1 workspace
      babylon macro init -w 3 azure                     # project/ with 3 workspaces
      babylon macro init --project-dir my-project azure # my-project/ with 1 workspace
      babylon macro init --project-dir my-proj -w 2 kob # my-proj/ with 2 workspaces on KOB

    \b
    arguments:

      cloud_provider: Target cloud provider for webapp deployment (e.g. 'azure', 'kob').
    """
    if num_workspaces < 1:
        logger.error("  [bold red]✘[/bold red] --workspaces must be >= 1", fg="red", bold=True)
        return

    root_path = Path.cwd()
    project_path = root_path / project_dir
    workspace_names = [f"workspace-{i}" for i in range(1, num_workspaces + 1)]

    # Validation mode: project folder already exists scaffold only missing pieces.
    if (project_path / "core").exists():
        logger.info(f"  [green]✔[/green] Project [cyan]{project_dir}/[/cyan] already exists running validation checks.")
        _ensure_webapp(root_path / _TF_WEBAPP_DIR, tf_webapp_version)
        for ws_name in workspace_names:
            ws_index = ws_name.split("-")[-1]
            ws_vars = project_path / "workspaces" / ws_name / f"variables-{ws_index}.yaml"
            if not ws_vars.exists():
                logger.warning(f"  [yellow]⚠[/yellow] Workspace [cyan]{ws_name}[/cyan] not found scaffolding it now.")
                _scaffold_workspace(project_path / "workspaces", ws_name, cloud_provider)
            else:
                logger.info(f"  [green]✔[/green] Workspace [cyan]{ws_name}[/cyan] already exists.")
        return

    # Scaffold mode: build everything from scratch.
    _scaffold_project(root_path, project_dir, num_workspaces, cloud_provider, tf_webapp_version)


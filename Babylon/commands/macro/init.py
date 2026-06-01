import subprocess
from logging import getLogger
from pathlib import Path
from shutil import copy

from click import Choice, argument, command, echo, option, style

from Babylon.utils.environment import Environment

logger = getLogger(__name__)
env = Environment()

# Constants

_TF_WEBAPP_DIR = "terraform-webapp"
_TF_WEBAPP_REPO_URL = "https://github.com/Cosmo-Tech/terraform-webapp.git"
_TF_WEBAPP_DEFAULT_VERSION = "0.2.0"
_VARIABLES_TEMPLATE = "variables.yaml"

_PROJECT_YAML_FILES = [
    "Organization.yaml",
    "Solution.yaml",
    "Workspace.yaml",
]

# Dashboard sub-directories to scaffold under <project>/dashboard/
_DASHBOARD_PROVIDERS = ["superset", "powerbi"]
_SUPPORTED_CLOUD_PROVIDERS = {"azure", "kob"}

# Private helpers


def _get_provider_template(cloud_provider: str, filename: str) -> Path:
    """Return the template path for *filename* scoped to *cloud_provider* when available,
    falling back to the shared yaml directory otherwise."""
    provider = cloud_provider.lower()
    if provider in _SUPPORTED_CLOUD_PROVIDERS:
        return env.original_template_path / "yaml" / provider / filename
    return env.original_template_path / "yaml" / filename


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


def _ensure_variables_file(variables_path: Path, variables_file: str, cloud_provider: str) -> None:
    """Log success when *variables_path* exists, otherwise copy the template."""
    if variables_path.exists():
        logger.info(f"  [green]✔[/green] Variables file [cyan]{variables_file}[/cyan] already exists.")
        return

    logger.warning("  [bold yellow]![/bold yellow] Variables file not found")
    logger.info("  [dim]→ Generating variables file from template...[/dim]")
    try:
        variables_template = _get_provider_template(cloud_provider, _VARIABLES_TEMPLATE)
        copy(variables_template, variables_path)
        if variables_path.exists():
            logger.info(f"  [green]✔[/green] Generated [cyan]{variables_file}[/cyan]")
        else:
            logger.error(f"  [bold red]✘[/bold red] Failed to generate [cyan]{variables_file}[/cyan]")
    except OSError as exc:
        logger.error(f"  [bold red]✘[/bold red] Failed to generate variables file: {exc}")


def _scaffold_project(
    project_path: Path, variables_path: Path, variables_file: str, tf_webapp_path: Path, cloud_provider: str, tf_webapp_version: str
) -> None:
    """Create the full project directory structure and copy all template files."""
    try:
        _create_project_dir(project_path)
        _copy_yaml_templates(project_path, cloud_provider)
        _create_postgres_jobs(project_path)
        _create_dashboard_dirs(project_path)
        _copy_variables_template(variables_path, variables_file, cloud_provider)
        _ensure_webapp(tf_webapp_path, tf_webapp_version)
        _print_success_summary(project_path, variables_file)
    except OSError as exc:
        logger.error("  [bold red]✘[/bold red] An error occurred while scaffolding see babylon logs for details")
        logger.debug(f"  [bold red]✘[/bold red] Error details: {exc}", exc_info=True)


def _create_project_dir(project_path: Path) -> None:
    project_path.mkdir(parents=True, exist_ok=True)
    if project_path.exists():
        logger.info(f"  [dim]→ Created directory: {project_path}[/dim]")
    else:
        logger.error(f"  [bold red]✘[/bold red] Failed to create directory: {project_path}")


def _copy_yaml_templates(project_path: Path, cloud_provider: str) -> None:
    for filename in _PROJECT_YAML_FILES:
        src = env.original_template_path / "yaml" / filename
        copy(src, project_path / filename)
        logger.info(f"  [green]✔[/green] Generated [white]{filename}[/white]")

    # Copy the cloud-provider-specific Webapp.yaml
    webapp_src = _get_provider_template(cloud_provider, "Webapp.yaml")
    copy(webapp_src, project_path / "Webapp.yaml")
    logger.info(f"  [green]✔[/green] Generated [white]Webapp.yaml[/white] (provider: {cloud_provider})")


def _create_postgres_jobs(project_path: Path) -> None:
    postgres_jobs_path = project_path / "postgres" / "jobs"
    postgres_jobs_path.mkdir(parents=True, exist_ok=True)
    if postgres_jobs_path.exists():
        logger.info("  [dim]→ Created directory: postgres/jobs[/dim]")
    else:
        logger.error("  [bold red]✘[/bold red] Failed to create directory: postgres/jobs")

    k8s_template = env.original_template_path / "yaml" / "k8s_job.yaml"
    if k8s_template.exists():
        copy(k8s_template, postgres_jobs_path / "k8s_job.yaml")
        logger.info("  [green]✔[/green] Generated [white]postgres/jobs/k8s_job.yaml[/white]")


def _create_dashboard_dirs(project_path: Path) -> None:
    """Create dashboard/<provider>/ sub-directories for each supported provider."""
    for provider in _DASHBOARD_PROVIDERS:
        provider_path = project_path / "dashboard" / provider
        provider_path.mkdir(parents=True, exist_ok=True)
        if provider_path.exists():
            logger.info(f"  [dim]→ Created directory: dashboard/{provider}[/dim]")
        else:
            logger.error(f"  [bold red]✘[/bold red] Failed to create directory: dashboard/{provider}")


def _copy_variables_template(variables_path: Path, variables_file: str, cloud_provider: str) -> None:
    variables_template = _get_provider_template(cloud_provider, _VARIABLES_TEMPLATE)
    copy(variables_template, variables_path)
    if variables_path.exists():
        logger.info(f"  [green]✔[/green] Generated [white]{variables_file}[/white] (provider: {cloud_provider})")
    else:
        logger.error(f"  [bold red]✘[/bold red] Failed to generate [white]{variables_file}[/white]")


def _print_success_summary(project_path: Path, variables_file: str) -> None:
    echo(style("\n🚀 Project successfully initialized!", fg="green", bold=True))
    echo(style(f"   Path: {project_path}", fg="white", dim=True))
    echo(style("\nNext steps:", fg="white", bold=True))
    echo(style(f"  1. Edit your variables in {variables_file}", fg="cyan"))
    echo(style("  2. Run your first deployment command", fg="cyan"))


@command()
@option("--project-folder", default="project", help="Name of the project folder to create (default: 'project').")
@option("--variables-file", default="variables.yaml", help="Name of the variables file (default: 'variables.yaml').")
@option(
    "--tf-webapp-version",
    "tf_webapp_version",
    default=_TF_WEBAPP_DEFAULT_VERSION,
    show_default=True,
    help=f"Version (tag) of the terraform-webapp module to clone/checkout. Default: {_TF_WEBAPP_DEFAULT_VERSION}.",
)
@argument("cloud_provider", type=Choice(["azure", "kob"], case_sensitive=False))
def init(project_folder: str, variables_file: str, tf_webapp_version: str, cloud_provider: str):
    """
    Scaffolds a new Babylon project structure using YAML templates.

    arguments:

      cloud_provider: Target cloud provider for webapp deployment (e.g. 'azure', 'kob').
    """
    cwd = Path.cwd()
    project_path = cwd / project_folder
    variables_path = cwd / variables_file
    tf_webapp_path = cwd / _TF_WEBAPP_DIR

    # Validation mode: project folder already exists — check each component.
    if project_path.exists():
        logger.info(f"  [green]✔[/green] Project directory [cyan]{project_folder}[/cyan] already exists.")
        _ensure_webapp(tf_webapp_path, tf_webapp_version)
        _ensure_variables_file(variables_path, variables_file, cloud_provider)
        return None

    # Scaffold mode: nothing exists yet — build everything from scratch.
    _scaffold_project(project_path, variables_path, variables_file, tf_webapp_path, cloud_provider, tf_webapp_version)

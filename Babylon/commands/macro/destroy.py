import subprocess
from logging import getLogger
from pathlib import Path
from string import Template
from typing import Callable

from click import command, echo, option, style
from kubernetes import client, utils
from kubernetes import config as kube_config
from yaml import safe_load

from Babylon.commands.api.organization import get_organization_api_instance
from Babylon.commands.api.solution import get_solution_api_instance
from Babylon.commands.api.workspace import get_workspace_api_instance
from Babylon.commands.macro.deploy import get_postgres_service_host, resolve_inclusion_exclusion
from Babylon.utils.credentials import get_keycloak_token
from Babylon.utils.decorators import injectcontext, retrieve_state
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)
env = Environment()


def _destroy_schema(schema_name: str, state: dict) -> None:
    """
    Destroy PostgreSQL schema for a workspace.
    """
    if not schema_name:
        logger.warning("  [yellow]⚠[/yellow] [dim]No schema found ! skipping deletion[/dim]")
        return
    workspace_id_tmp = f"{schema_name.replace('_', '-')}"
    db_host = get_postgres_service_host(env.environ_id)
    logger.info(f"  [dim]→ Destroying postgreSQL schema for workspace {workspace_id_tmp}...[/dim]")

    pg_config = env.get_config_from_k8s_secret_by_tenant("postgresql-config", env.environ_id)
    api_config = env.get_config_from_k8s_secret_by_tenant("postgresql-cosmotechapi", env.environ_id)

    if not pg_config or not api_config:
        logger.error("  [bold red]✘[/bold red] Failed to retrieve postgreSQL configuration from secrets")
        return

    mapping = {
        "namespace": env.environ_id,
        "db_host": db_host,
        "db_port": "5432",
        "cosmotech_api_database": api_config.get("database-name"),
        "cosmotech_api_admin_username": api_config.get("admin-username"),
        "cosmotech_api_admin_password": api_config.get("admin-password"),
        "cosmotech_api_writer_username": api_config.get("writer-username"),
        "cosmotech_api_reader_username": api_config.get("reader-username"),
        "workspace_schema": schema_name,
        "job_name": workspace_id_tmp,
    }
    destroy_jobs = env.original_template_path / "yaml" / "k8s_job_destroy.yaml"
    k8s_job_name = f"postgresql-destroy-{workspace_id_tmp}"
    kube_config.load_kube_config()
    k8s_client = client.ApiClient()
    with open(destroy_jobs, "r") as f:
        raw_content = f.read()

    templated_yaml = Template(raw_content).safe_substitute(mapping)
    yaml_dict = safe_load(templated_yaml)
    logger.info("  [dim]→ Applying kubernetes destroy job...[/dim]")
    try:
        utils.create_from_dict(k8s_client, yaml_dict, namespace=env.environ_id)
        logger.info(f"  [dim]→ Waiting for job [cyan]{k8s_job_name}[/cyan] to complete...[/dim]")
        wait_process = subprocess.run(
            [
                "kubectl",
                "wait",
                "--for=condition=complete",
                "job",
                k8s_job_name,
                f"--namespace={env.environ_id}",
                "--timeout=300s",
            ],
            capture_output=True,
            text=True,
        )
        if wait_process.returncode == 0:
            # Job completed, now check the logs for error
            logger.info("  [dim]→ Checking job logs for errors...[/dim]")
            logs_process = subprocess.run(
                ["kubectl", "logs", f"job/{k8s_job_name}", "-n", env.environ_id],
                capture_output=True,
                text=True,
            )
            if logs_process.returncode == 0:
                job_logs = logs_process.stdout if logs_process.stdout else logs_process.stderr
                if "ERROR" in job_logs or "error" in job_logs:
                    logger.error("  [bold red]✘[/bold red] Schema destruction failed inside the container")
                    logger.debug(f"  [bold red]✘[/bold red] Job logs : {job_logs}")
                elif "does not exist" in job_logs:
                    logger.info(
                        f"  [yellow]⚠[/yellow] [dim]Schema [magenta]{schema_name}[/magenta] does not exist (nothing to clean)[/dim]"
                    )
                    state["services"]["postgres"]["schema_name"] = ""
                else:
                    logger.info(f"  [green]✔[/green] Schema destruction [magenta]{schema_name}[/magenta] completed successfully")
                    state["services"]["postgres"]["schema_name"] = ""
            else:
                logger.error(f"  [bold red]✘[/bold red] Failed to retrieve logs for job {k8s_job_name}")
                logger.debug(f"  [bold red]✘[/bold red] Logs retrieval output {logs_process.stdout} {logs_process.stderr}")

        else:
            logger.error(f"  [bold red]✘[/bold red] Job {k8s_job_name} did not complete successfully see babylon logs for details")
            logger.debug(f"  [bold red]✘[/bold red] Job wait output {wait_process.stdout} {wait_process.stderr}")

    except Exception as e:
        logger.error("  [bold red]✘[/bold red] Unexpected error please check babylon logs file for details")
        logger.debug(f"  [bold red]✘[/bold red] {e}")


def _destroy_webapp(state: dict):
    """Terraform Destroy webapp"""
    logger.info("  [dim]→ Running Terraform destroy for WebApp resources...[/dim]")
    webapp_state = state.get("services", {}).get("webapp", {})
    webapp_neme = webapp_state.get("webapp_name")
    if not webapp_neme:
        logger.warning("  [yellow]⚠[/yellow] [dim]No WebApp found in state! skipping deletion [dim]")
        return
    tf_dir = Path(str(env.working_dir)).parent / "terraform-webapp"

    if not tf_dir.exists():
        logger.error(f"  [bold red]✘[/bold red] Terraform directory not found at {tf_dir}")
        return
    try:
        process = subprocess.Popen(
            ["terraform", "destroy", "-auto-approve"],
            cwd=tf_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        line_handlers = {
            "Destroy complete!": "green",
            "Resources:": "green",
            "Error": "red",
        }

        for line in process.stdout:
            clean_line = line.strip()
            if not clean_line:
                continue

            color = next((color for key, color in line_handlers.items() if key in clean_line), "white")
            bold = color == "red"
            echo(style(f"   {clean_line}", fg=color, bold=bold))

        process.wait()
        if process.returncode == 0:
            # Nettoyage du state webapp
            state["services"]["webapp"]["webapp_name"] = ""
            state["services"]["webapp"]["webapp_url"] = ""
            logger.info(f"   [green]✔[/green] WebApp [magenta]{webapp_neme}[/magenta] destroyed")
        else:
            logger.error(f"  [bold red]✘[/bold red] Terraform destroy failed (Code {process.returncode})")

    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Error during WebApp destruction: {e}")


def _delete_resource(
    api_call: Callable[..., None], resource_name: str, org_id: str | None, resource_id: str, state: dict, state_key: str
):
    """Helper to handle repetitive deletion logic and error handling."""
    if not resource_id:
        logger.warning(f"  [yellow]⚠[/yellow] [dim]No {resource_name} ID found in state! skipping deletion[dim]")
        return

    try:
        logger.info(f"  [dim]→ Existing ID [bold cyan]{resource_id}[/bold cyan] found. Deleting...[/dim]")
        if org_id and resource_name != "Organization":
            api_call(organization_id=org_id, **{f"{resource_name.lower()}_id": resource_id})
        else:
            api_call(organization_id=resource_id)

        logger.info(f"  [bold green]✔[/bold green] {resource_name} [magenta]{resource_id}[/magenta] deleted")
        state["services"]["api"][state_key] = ""
    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg or "Not Found" in error_msg:
            logger.info(f"  [bold yellow]⚠[/bold yellow] {resource_name} [magenta]{resource_id}[/magenta] already deleted (404)")
            state["services"]["api"][state_key] = ""
        else:
            logger.error(f"  [bold red]✘[/bold red] Error deleting {resource_name.lower()} {resource_id} reason: {e}")


@command()
@injectcontext()
@retrieve_state
@option("--include", "include", multiple=True, type=str, help="Specify the resources to destroy.")
@option("--exclude", "exclude", multiple=True, type=str, help="Specify the resources to exclude from destruction.")
def destroy(state: dict, include: tuple[str], exclude: tuple[str]):
    """Macro Destroy"""
    organization, solution, workspace, webapp = resolve_inclusion_exclusion(include, exclude)
    # Header for the destructive operation
    echo(style(f"\n🔥 Starting Destruction Process in namespace: {env.environ_id}", bold=True, fg="red"))
    keycloak_token, config = get_keycloak_token()

    # We need the Org ID for most sub-resource deletions
    api_state = state["services"]["api"]
    schema_state = state["services"]["postgres"]
    org_id = api_state["organization_id"]

    if solution:
        api = get_solution_api_instance(config=config, keycloak_token=keycloak_token)
        _delete_resource(api.delete_solution, "Solution", org_id, api_state["solution_id"], state, "solution_id")

    if workspace:
        _destroy_schema(schema_state["schema_name"], state)
        api = get_workspace_api_instance(config=config, keycloak_token=keycloak_token)
        _delete_resource(api.delete_workspace, "Workspace", org_id, api_state["workspace_id"], state, "workspace_id")

    if organization:
        api = get_organization_api_instance(config=config, keycloak_token=keycloak_token)
        _delete_resource(api.delete_organization, "Organization", None, org_id, state, "organization_id")

    if webapp:
        _destroy_webapp(state)

    # --- State Persistence ---
    env.store_state_in_local(state=state)
    if state.get("remote"):
        logger.info("  [dim]☁ Syncing state cleanup to cloud...[/dim]")
        env.set_blob_client()
        env.store_state_in_cloud(state=state)

    # --- Final Destruction Summary ---
    echo(style("\n📋 Destruction Summary", bold=True, fg="white"))
    final_state = env.get_state_from_local()
    services = final_state.get("services")
    api_data = services.get("api")
    for key, value in api_data.items():
        # Prepare the label (e.g., "Organization Id")
        label_text = f"  • {key.replace('_', ' ').title()}"
        # We check if the ID is now empty (which means it was deleted)
        status = "DELETED" if not value else value
        color = "red" if status == "DELETED" else "green"
        echo(f"{style(f'{label_text:<20}:', fg='cyan', bold=True)} {style(status, fg=color)}")

    # Affichage WebApp
    webapp_data = services.get("webapp", {})
    webapp_id = webapp_data.get("webapp_name")
    label_text = "  • Webapp Name"
    status = "DELETED" if not webapp_id else webapp_id
    color = "red" if status == "DELETED" else "green"
    echo(f"{style(f'{label_text:<20}:', fg='cyan', bold=True)} {style(status, fg=color)}")

    echo(style("\n✨ Cleanup process complete", fg="white", bold=True))
    return CommandResponse.success()

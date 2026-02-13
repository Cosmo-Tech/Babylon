import subprocess
from json import dumps
from logging import getLogger
from pathlib import Path as PathlibPath
from string import Template

from click import echo, style
from cosmotech_api.models.workspace_create_request import WorkspaceCreateRequest
from cosmotech_api.models.workspace_security import WorkspaceSecurity
from cosmotech_api.models.workspace_update_request import WorkspaceUpdateRequest
from kubernetes import client, utils
from kubernetes import config as kube_config
from kubernetes.utils import FailToCreateError
from yaml import safe_load

from Babylon.commands.api.workspace import get_workspace_api_instance
from Babylon.commands.macro.deploy import get_postgres_service_host, update_object_security
from Babylon.utils.credentials import get_keycloak_token
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)
env = Environment()


def deploy_workspace(namespace: str, file_content: str, deploy_dir: PathlibPath) -> bool:
    echo(style(f"\n🚀 Deploying Workspace in namespace: {env.environ_id}", bold=True, fg="cyan"))

    # Retrieve the state
    env.get_ns_from_text(content=namespace)
    state = env.retrieve_state_func()
    content = env.fill_template(data=file_content, state=state)

    # Authentication and API client initialization
    keycloak_token, config = get_keycloak_token()
    payload: dict = content.get("spec").get("payload")
    api_section = state["services"]["api"]
    # Determine if we are performing a Create or Update based on state
    api_section["workspace_id"] = payload.get("id") or api_section.get("workspace_id", "")
    spec = {}
    spec["payload"] = dumps(payload, indent=2, ensure_ascii=True)
    api_instance = get_workspace_api_instance(config=config, keycloak_token=keycloak_token)

    # --- Deployment Logic ---
    if not api_section["workspace_id"]:
        # Case: New Workspace
        logger.info("  [dim]→ No existing workspace ID found. Creating...[/dim]")
        workspace_create_request = WorkspaceCreateRequest.from_dict(payload)
        workspace = api_instance.create_workspace(
            organization_id=api_section["organization_id"], workspace_create_request=workspace_create_request
        )
        if workspace is None:
            logger.error("  [bold red]✘[/bold red] Failed to create workspace")
            return CommandResponse.fail()
        # Save the newly generated ID to state
        logger.info(f"  [bold green]✔[/bold green] Workspace [bold magenta]{workspace.id}[/bold magenta] created")
        state["services"]["api"]["workspace_id"] = workspace.id
    else:
        # Case: Update Existing Workspace
        logger.info(f"  [dim]→ Existing ID [bold cyan]{api_section['workspace_id']}[/bold cyan] found. Updating...[/dim]")
        workspace_update_request = WorkspaceUpdateRequest.from_dict(payload)
        updated = api_instance.update_workspace(
            organization_id=api_section["organization_id"],
            workspace_id=api_section["workspace_id"],
            workspace_update_request=workspace_update_request,
        )
        if updated is None:
            logger.error(f"  [bold red]✘[/bold red] Failed to update workspace {api_section['workspace_id']}")
            return CommandResponse.fail()
        # Handle Security Policy synchronization if provided in payload
        if payload.get("security"):
            try:
                logger.info("  [dim]→ Syncing security policies...[/dim]")
                current_security = api_instance.get_workspace_security(
                    organization_id=api_section["organization_id"], workspace_id=api_section["workspace_id"]
                )
                update_object_security(
                    "workspace",
                    current_security=current_security,
                    desired_security=WorkspaceSecurity.from_dict(payload.get("security")),
                    api_instance=api_instance,
                    object_id=[api_section["organization_id"], api_section["workspace_id"]],
                )
            except Exception as e:
                logger.error(f"  [bold red]✘[/bold red] Security update failed: {e}")
                return CommandResponse.fail()
        logger.info(f"  [bold green]✔[/bold green] Workspace [bold magenta]{api_section['workspace_id']}[/bold magenta] updated")
    workspace_id = state["services"]["api"]["workspace_id"]
    spec = content.get("spec") or {}
    sidecars = spec.get("sidecars") or {}
    postgres_section = sidecars.get("postgres") or {}
    schema_config = postgres_section.get("schema") or {}
    should_create_schema = schema_config.get("create", False)
    if should_create_schema:
        db_host = get_postgres_service_host(env.environ_id)
        logger.info(f"  [dim]→ Initializing PostgreSQL schema for workspace {workspace_id}...[/dim]")
        pg_config = env.get_config_from_k8s_secret_by_tenant("postgresql-config", env.environ_id)
        api_config = env.get_config_from_k8s_secret_by_tenant("postgresql-cosmotechapi", env.environ_id)
        if pg_config and api_config:
            schema_name = f"{workspace_id.replace('-', '_')}"
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
                "job_name": workspace_id,
            }
            jobs = schema_config.get("jobs", [])
            if not isinstance(deploy_dir, PathlibPath):
                deploy_dir = PathlibPath(deploy_dir)
            for job in jobs:
                script_path = deploy_dir / job.get("path", "") / job.get("name", "")
                if script_path.exists():
                    kube_config.load_kube_config()
                    k8s_client = client.ApiClient()
                    k8s_job_name = f"postgresql-init-{workspace_id}"
                    with open(script_path, "r") as f:
                        raw_content = f.read()
                    templated_yaml = Template(raw_content).safe_substitute(mapping)
                    yaml_dict = safe_load(templated_yaml)
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
                                "--timeout=50s",
                            ],
                            capture_output=True,
                            text=True,
                        )
                        if wait_process.returncode != 0:
                            logger.error(
                                f"  [bold red]✘[/bold red] Job {k8s_job_name} did not complete successfully"
                                f" see babylon logs for details"
                            )
                            logger.debug(f"  [bold red]✘[/bold red] Job wait output {wait_process.stdout} {wait_process.stderr}")
                        else:
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
                                    logger.error("  [bold red]✘[/bold red] Schema creation failed inside the container")
                                    logger.debug(f"  [bold red]✘[/bold red] Job logs : {job_logs}")
                                elif "already exists" in job_logs:
                                    logger.info(
                                        f"  [yellow]⚠[/yellow] [dim]Schema [magenta]{schema_name}[/magenta]"
                                        f" already exists (skipping creation)[/dim]"
                                    )
                                else:
                                    logger.info(
                                        f"  [green]✔[/green] Schema creation [magenta]{schema_name}[/magenta] completed successfully"
                                    )
                                    state["services"]["postgres"]["schema_name"] = schema_name
                            else:
                                logger.error(f" [bold red]✘[/bold red] Failed to retrieve logs for job {k8s_job_name}")
                                logger.debug(
                                    f" [bold red]✘[/bold red] Logs retrieval output {logs_process.stdout} {logs_process.stderr}"
                                )

                    except FailToCreateError as e:
                        for inner_exception in e.api_exceptions:
                            if inner_exception.status == 409:
                                logger.warning(f"  [yellow]⚠[/yellow] [dim]Job [cyan]{k8s_job_name}[/cyan] already exists.[/dim]")
                            else:
                                logger.error(
                                    f"  [bold red]✘[/bold red] K8s Error ({inner_exception.status}): {inner_exception.reason}"
                                )
                                logger.debug(f"  Detail: {inner_exception.body}")
                    except Exception as e:
                        logger.error("  [bold red]✘[/bold red] Unexpected error please check babylon logs file for details")
                        logger.debug(f"  [bold red]✘[/bold red] {e}")

    # --- State Persistence ---
    # Ensure the local and remote states are synchronized after successful API calls
    env.store_state_in_local(state)
    if env.remote:
        env.store_state_in_cloud(state)

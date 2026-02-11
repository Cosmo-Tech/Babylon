from json import dumps
from logging import getLogger
from string import Template
import subprocess
import sys

from pathlib import Path as PathlibPath
from click import echo, style
from cosmotech_api.models.workspace_create_request import WorkspaceCreateRequest
from cosmotech_api.models.workspace_security import WorkspaceSecurity
from cosmotech_api.models.workspace_update_request import WorkspaceUpdateRequest

from Babylon.commands.api.workspace import get_workspace_api_instance
from Babylon.commands.macro.deploy import update_object_security, get_postgres_service_host
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
        logger.info(
            f"  [dim]→ Existing ID [bold cyan]{api_section['workspace_id']}[/bold cyan] found. Updating...[/dim]"
        )
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
        logger.info(
            f"  [bold green]✔[/bold green] Workspace [bold magenta]{api_section['workspace_id']}[/bold magenta] updated"
        )
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
                "job_name": workspace_id
            }
            jobs = schema_config.get("jobs", [])
            if not isinstance(deploy_dir, PathlibPath):
                deploy_dir = PathlibPath(deploy_dir)
            for job in jobs:
                script_path = deploy_dir / job.get("path", "") / job.get("name", "")
                if script_path.exists():
                    try: 
                        with open(script_path, 'r') as f:
                            raw_content = f.read()

                        templated_yaml = Template(raw_content).safe_substitute(mapping)
                        process = subprocess.run(
                            ["kubectl", "apply", "-f", "-"],
                            input=templated_yaml,
                            capture_output=True,
                            text=True,
                        )

                        if process.returncode == 0:
                            logger.info(f"  [bold green]✔[/bold green] Job [cyan]{job.get('name')}[/cyan] applied for schema [magenta]{schema_name}[/magenta]")
                        else:
                            logger.error(f"  [bold red]✘[/bold red] Failed to apply job [blue]{job.get('name')}[/blue]\n")
                            logger.error(f"  [bold magenta]stderr[/bold magenta]: {process.stderr.strip()}")
                    except Exception as e:
                        logger.error(f"  [bold red]✘[/bold red] Error processing job [cyan]{job.get('name')}[/cyan]: {e}")
                else:
                    logger.error(f"  [bold red]✘[/bold red] Script not found [magenta]{script_path}[/magenta]")

    # --- State Persistence ---
    # Ensure the local and remote states are synchronized after successful API calls
    env.store_state_in_local(state)
    if env.remote:
        env.store_state_in_cloud(state)

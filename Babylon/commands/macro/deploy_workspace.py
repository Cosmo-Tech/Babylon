from json import dumps
from logging import getLogger

from click import echo, style
from cosmotech_api.models.workspace_create_request import WorkspaceCreateRequest
from cosmotech_api.models.workspace_security import WorkspaceSecurity
from cosmotech_api.models.workspace_update_request import WorkspaceUpdateRequest

from Babylon.commands.api.client import get_workspace_api_instance
from Babylon.commands.macro.deploy import update_object_security
from Babylon.utils.credentials import get_keycloak_token
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)
env = Environment()


def deploy_workspace(namespace: str, file_content: str) -> bool:
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
    # --- State Persistence ---
    # Ensure the local and remote states are synchronized after successful API calls
    env.store_state_in_local(state)
    if env.remote:
        env.store_state_in_cloud(state)

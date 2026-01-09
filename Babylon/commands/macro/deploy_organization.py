from json import dumps
from logging import getLogger

from click import echo, style
from cosmotech_api.models.organization_create_request import OrganizationCreateRequest
from cosmotech_api.models.organization_security import OrganizationSecurity
from cosmotech_api.models.organization_update_request import OrganizationUpdateRequest

from Babylon.commands.api.organization import get_organization_api_instance
from Babylon.commands.macro.deploy import update_object_security
from Babylon.utils.credentials import get_keycloak_token
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)
env = Environment()


def deploy_organization(namespace: str, file_content: str):
    echo(style(f"\n🚀 Deploying Organization in namespace: {env.environ_id}", bold=True, fg="cyan"))

    # Retrieve the state
    env.get_ns_from_text(content=namespace)
    state = env.retrieve_state_func()
    content = env.fill_template(data=file_content, state=state)

    # Authentication and API client initialization
    keycloak_token, config = get_keycloak_token()
    payload: dict = content.get("spec").get("payload", {})
    api_section = state["services"]["api"]

    # Determine if we are performing a Create or Update based on state
    api_section["organization_id"] = payload.get("id") or api_section.get("organization_id", "")
    spec = {}
    spec["payload"] = dumps(payload, indent=2, ensure_ascii=True)
    api_instance = get_organization_api_instance(config=config, keycloak_token=keycloak_token)

    # --- Deployment Logic ---
    if not api_section["organization_id"]:
        # Case: New Organization
        logger.info("  [dim]→ No existing organization ID found. Creating...[/dim]")
        organization_create_request = OrganizationCreateRequest.from_dict(payload)
        organization = api_instance.create_organization(organization_create_request)
        if organization is None:
            logger.error("  [bold red]✘[/bold red] Failed to create organization")
            return CommandResponse.fail()
        # Save the newly generated ID to state
        logger.info(f"  [bold green]✔[/bold green] Organization [bold magenta]{organization.id}[/bold magenta] created")
        state["services"]["api"]["organization_id"] = organization.id
    else:
        # Case: Update Existing Organization
        logger.info(
            f"  [dim]→ Existing ID [bold cyan]{api_section['organization_id']}[/bold cyan] found. Updating...[/dim]"
        )
        organization_update_request = OrganizationUpdateRequest.from_dict(payload)
        updated = api_instance.update_organization(
            organization_id=api_section["organization_id"], organization_update_request=organization_update_request
        )
        if updated is None:
            logger.error(f"  [bold red]✘[/bold red] Failed to update organization {api_section['organization_id']}")
            return CommandResponse.fail()
        # Handle Security Policy synchronization if provided in payload
        if payload.get("security"):
            try:
                logger.info("  [dim]→ Syncing security policies...[/dim]")
                current_security = api_instance.get_organization_security(
                    organization_id=api_section["organization_id"]
                )
                update_object_security(
                    "organization",
                    current_security=current_security,
                    desired_security=OrganizationSecurity.from_dict(payload.get("security")),
                    api_instance=api_instance,
                    object_id=[api_section["organization_id"]],
                )
            except Exception as e:
                logger.error(f"  [bold red]✘[/bold red] Security update failed: {e}")
                return CommandResponse.fail()
        logger.info(
            f"  [bold green]✔[/bold green] Organization"
            f" [bold magenta]{api_section['organization_id']}[/bold magenta] updated"
        )
    # --- State Persistence ---
    # Ensure the local and remote states are synchronized after successful API calls
    env.store_state_in_local(state)
    if env.remote:
        env.store_state_in_cloud(state)

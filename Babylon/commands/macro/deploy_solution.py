from json import dumps
from logging import getLogger

from click import echo, style
from cosmotech_api.models.solution_create_request import SolutionCreateRequest
from cosmotech_api.models.solution_security import SolutionSecurity
from cosmotech_api.models.solution_update_request import SolutionUpdateRequest

from Babylon.commands.api.solution import get_solution_api_instance
from Babylon.commands.macro.deploy import update_object_security
from Babylon.utils.credentials import get_keycloak_token
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)
env = Environment()


def deploy_solution(namespace: str, file_content: str) -> bool:
    echo(style(f"\n🚀 Deploying Solution in namespace: {env.environ_id}", bold=True, fg="cyan"))

    # Retrieve the state
    env.get_ns_from_text(content=namespace)
    state = env.retrieve_state_func()
    content = env.fill_template(data=file_content, state=state)

    # Authentication and API client initialization
    keycloak_token, config = get_keycloak_token()
    payload: dict = content.get("spec").get("payload")
    api_section = state["services"]["api"]

    # Determine if we are performing a Create or Update based on state
    api_section["solution_id"] = payload.get("id") or api_section.get("solution_id", "")
    spec = {}
    spec["payload"] = dumps(payload, indent=2, ensure_ascii=True)
    api_instance = get_solution_api_instance(config=config, keycloak_token=keycloak_token)

    # --- Deployment Logic ---
    if not api_section["solution_id"]:
        # Case: New Solution
        logger.info("  [dim]→ No existing solution ID found. Creating...[/dim]")
        solution_create_request = SolutionCreateRequest.from_dict(payload)
        solution = api_instance.create_solution(
            organization_id=api_section["organization_id"], solution_create_request=solution_create_request
        )
        if solution is None:
            logger.error("  [bold red]✘[/bold red] Failed to create solution")
            return CommandResponse.fail()
        # Save the newly generated ID to state
        logger.info(f"  [bold green]✔[/bold green] Solution [bold magenta]{solution.id}[/bold magenta] created")
        state["services"]["api"]["solution_id"] = solution.id
    else:
        # Case: Update Existing Solution
        logger.info(f"  [dim]→ Existing ID [bold cyan]{api_section['solution_id']}[/bold cyan] found. Updating...[/dim]")
        solution_update_request = SolutionUpdateRequest.from_dict(payload)
        updated = api_instance.update_solution(
            organization_id=api_section["organization_id"],
            solution_id=api_section["solution_id"],
            solution_update_request=solution_update_request,
        )
        if updated is None:
            logger.error(f"  [bold red]✘[/bold red] Failed to update solution {api_section['solution_id']}")
            return CommandResponse.fail()
        # Handle Security Policy synchronization if provided in payload
        if payload.get("security"):
            try:
                logger.info("  [dim]→ Syncing security policies...[/dim]")
                current_security = api_instance.get_solution_security(
                    organization_id=api_section["organization_id"], solution_id=api_section["solution_id"]
                )
                update_object_security(
                    "solution",
                    current_security=current_security,
                    desired_security=SolutionSecurity.from_dict(payload.get("security")),
                    api_instance=api_instance,
                    object_id=[api_section["organization_id"], api_section["solution_id"]],
                )
            except Exception as e:
                logger.error(f"  [bold red]✘[/bold red] Security update failed: {e}")
                return CommandResponse.fail()
        logger.info(f"  [bold green]✔[/bold green] Solution [bold magenta]{api_section['solution_id']}[/bold magenta] updated")
    # --- State Persistence ---
    # Ensure the local and remote states are synchronized after successful API calls
    env.store_state_in_local(state)
    if env.remote:
        env.store_state_in_cloud(state)

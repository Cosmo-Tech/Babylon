from logging import getLogger

from click import command, echo, option, style

from Babylon.commands.api.organization import get_organization_api_instance
from Babylon.commands.api.solution import get_solution_api_instance
from Babylon.commands.api.workspace import get_workspace_api_instance
from Babylon.commands.macro.helpers.common import resolve_inclusion_exclusion
from Babylon.commands.macro.helpers.webapp import destroy_webapp
from Babylon.commands.macro.helpers.workspace import (
    delete_api_resource,
    delete_kubernetes_resources,
    destroy_postgres_schema,
)
from Babylon.utils.credentials import get_keycloak_token
from Babylon.utils.decorators import injectcontext, retrieve_state
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)
env = Environment()


@command()
@injectcontext()
@retrieve_state
@option("--include", "include", multiple=True, type=str, help="Specify the resources to destroy.")
@option("--exclude", "exclude", multiple=True, type=str, help="Specify the resources to exclude from destruction.")
def destroy(state: dict, include: tuple[str], exclude: tuple[str]):
    """Macro Destroy"""
    organization, solution, workspace, webapp = resolve_inclusion_exclusion(include, exclude)
    echo(style(f"\n🔥 Starting Destruction Process in namespace: {env.environ_id}", bold=True, fg="red"))
    keycloak_token, config = get_keycloak_token()

    api_state = state["services"]["api"]
    schema_state = state["services"]["postgres"]
    org_id = api_state["organization_id"]

    if solution:
        api = get_solution_api_instance(config=config, keycloak_token=keycloak_token)
        delete_api_resource(api.delete_solution, "Solution", org_id, api_state["solution_id"], state, "solution_id")

    if workspace:
        destroy_postgres_schema(schema_state["schema_name"], state)
        delete_kubernetes_resources(
            namespace=env.environ_id,
            organization_id=org_id,
            workspace_id=api_state["workspace_id"],
        )
        api = get_workspace_api_instance(config=config, keycloak_token=keycloak_token)
        delete_api_resource(api.delete_workspace, "Workspace", org_id, api_state["workspace_id"], state, "workspace_id")

    if organization:
        api = get_organization_api_instance(config=config, keycloak_token=keycloak_token)
        delete_api_resource(api.delete_organization, "Organization", None, org_id, state, "organization_id")

    if webapp:
        destroy_webapp(state)

    # --- State Persistence ---
    env.store_state_in_local(state=state)
    if state.get("remote"):
        logger.info("  [dim]☁ Syncing state cleanup to kubernetes...[/dim]")
        env.store_state_in_kubernetes(state=state)

    # --- Final Destruction Summary ---
    echo(style("\n📋 Destruction Summary", bold=True, fg="white"))
    final_state = env.get_state_from_local()
    services = final_state.get("services")
    api_data = services.get("api")
    for key, value in api_data.items():
        label_text = f"  • {key.replace('_', ' ').title()}"
        status = "DELETED" if not value else value
        color = "red" if status == "DELETED" else "green"
        echo(f"{style(f'{label_text:<20}:', fg='cyan', bold=True)} {style(status, fg=color)}")

    webapp_data = services.get("webapp", {})
    webapp_id = webapp_data.get("webapp_name")
    label_text = "  • Webapp Name"
    status = "DELETED" if not webapp_id else webapp_id
    color = "red" if status == "DELETED" else "green"
    echo(f"{style(f'{label_text:<20}:', fg='cyan', bold=True)} {style(status, fg=color)}")

    echo(style("\n✨ Cleanup process complete", fg="white", bold=True))
    return CommandResponse.success()

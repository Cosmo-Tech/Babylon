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
from Babylon.commands.macro.helpers.workspace.superset_helper import delete_superset_assets
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
        # --- Superset cleanup
        superset_url = (config.get("superset_url") or "").rstrip("/")
        if superset_url:
            logger.info("  [dim]→ Deleting Superset assets ...[/dim]")
            delete_superset_assets(
                base_url=superset_url,
                superset_config=config,
                workspace_id=api_state["workspace_id"],
            )
        else:
            logger.warning("  [yellow]⚠[/yellow] superset_url not configured skipping Superset cleanup")

        api = get_workspace_api_instance(config=config, keycloak_token=keycloak_token)
        delete_api_resource(api.delete_workspace, "Workspace", org_id, api_state["workspace_id"], state, "workspace_id")

    if organization:
        api = get_organization_api_instance(config=config, keycloak_token=keycloak_token)
        delete_api_resource(api.delete_organization, "Organization", None, org_id, state, "organization_id")

    if webapp:
        destroy_webapp(state)

    # ------------------------------------------------------------------
    # Determine whether ALL tracked resources have been cleared.
    # This single flag drives both local-state and remote-state cleanup:
    #   - partial destroy  → at least one ID is still populated → keep states
    #   - complete destroy → every ID is empty → delete states
    # ------------------------------------------------------------------
    svc = state.get("services", {})
    api_ids = svc.get("api", {})
    all_resources_cleared = (
        not api_ids.get("organization_id")
        and not api_ids.get("solution_id")
        and not api_ids.get("workspace_id")
        and not svc.get("webapp", {}).get("webapp_name", "")
        and not svc.get("postgres", {}).get("schema_name", "")
    )

    # --- Local state cleanup ---
    if all_resources_cleared:
        logger.info("  [dim]🗑 All resources cleared ! removing local state file...[/dim]")
        if not env.delete_state_in_local():
            logger.warning(
                "  [yellow]⚠[/yellow] Could not delete the local state file ! "
                "destroy succeeded but the file may need manual cleanup."
            )
    else:
        logger.info("  [dim]🗑 Partial destroy ! persisting updated state locally...[/dim]")
        env.store_state_in_local(state=state)

    # --- Remote state cleanup ---
    # Follows exactly the same rule: delete on full destroy, update on partial.
    if state.get("remote"):
        if all_resources_cleared:
            logger.info("  [dim]☁ All resources cleared ! removing remote state secret from Kubernetes...[/dim]")
            deleted = env.delete_state_in_kubernetes()
            if not deleted:
                logger.warning(
                    "  [yellow]⚠[/yellow] Could not delete the remote state secret — "
                    "destroy succeeded but the secret may need manual cleanup."
                )
        else:
            logger.info("  [dim]☁ Partial destroy ! syncing updated state to Kubernetes...[/dim]")
            env.store_state_in_kubernetes(state=state)

    # --- Final Destruction Summary ---
    echo(style("\n📋 Destruction Summary", bold=True, fg="white"))
    # Use the in-memory state (already up-to-date) rather than re-reading local
    # which could be stale when remote mode is active.
    final_state = state
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

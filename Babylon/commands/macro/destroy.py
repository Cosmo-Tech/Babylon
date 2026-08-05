from logging import getLogger

from click import command, confirm, echo, option, style

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


def _build_targeted_resources(state: dict, organization: bool, solution: bool, workspace: bool, webapp: bool) -> list[tuple[str, str]]:
    """Map active resource flags to their (label, current-ID) pairs from the state."""
    api_state = state["services"]["api"]
    webapp_state = state["services"].get("webapp", {})
    resource_map = [
        (organization, "Organization", api_state.get("organization_id") or "(NOT DEPLOYED)"),
        (solution, "Solution", api_state.get("solution_id") or "(NOT DEPLOYED)"),
        (workspace, "Workspace", api_state.get("workspace_id") or "(NOT DEPLOYED)"),
        (webapp, "Web App", webapp_state.get("webapp_name") or "(NOT DEPLOYED)"),
    ]
    return [(label, value) for flag, label, value in resource_map if flag]


def _build_scope_message(include: tuple[str, ...], exclude: tuple[str, ...], targeted: list[tuple[str, str]]) -> str:
    """Return a human-readable sentence describing the destroy scope."""
    if include:
        names = " and ".join(label.lower() for label, _ in targeted)
        return f"Only the selected {names} will be destroyed."
    if exclude:
        excluded_names = " and ".join(exclude)
        return f"All resources will be destroyed except the selected {excluded_names}."
    return "All resources in this environment will be destroyed."


def _confirm_destroy(
    include: tuple[str, ...],
    exclude: tuple[str, ...],
    targeted: list[tuple[str, str]],
    yes: bool = False,
) -> bool:
    """Display the destruction warning banner and prompt the user for confirmation.

    When *yes* is True the prompt is skipped and True is returned immediately,
    which is useful for automated environments and unit tests.

    Returns True if the destruction should proceed, False if the user cancelled.
    """
    scope_msg = _build_scope_message(include, exclude, targeted)

    echo()
    echo(style("  ╭─────────────────────────────────────────────────────────────╮", fg="red"))
    echo(style("  │  ⚠  DESTRUCTIVE ACTION                                      │", fg="red", bold=True))
    echo(style("  ╰─────────────────────────────────────────────────────────────╯", fg="red"))
    echo()
    echo(f"  State        {style(f'state-{env.context_id}-{env.environ_id}', fg='cyan', bold=True)}")
    echo()
    echo(style("  Resources to be destroyed:", fg="white", bold=True))
    for label, value in targeted:
        echo(f"    {style('•', fg='red')} {style(label + ':', fg='cyan'):<22} {style(value, fg='white')}")
    echo()
    echo(style(f"  {scope_msg}", fg="yellow"))
    echo(style("  This action cannot be undone.", fg="red", bold=True))
    echo()

    if yes:
        echo(style("  --yes flag detected ! skipping interactive confirmation.", fg="yellow"))
        return True

    return confirm(
        style("  Continue with destruction?", fg="white", bold=True),
        default=False,
    )


def _destroy_workspace_resources(state: dict, config: dict, keycloak_token: str, org_id: str) -> None:
    """Delete all workspace-level resources: Postgres schema, Kubernetes resources,
    Superset assets, and the Workspace API object."""
    api_state = state["services"]["api"]
    schema_state = state["services"]["postgres"]

    destroy_postgres_schema(schema_state["schema_name"], state)
    delete_kubernetes_resources(
        namespace=env.environ_id,
        organization_id=org_id,
        workspace_id=api_state["workspace_id"],
    )

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


def _execute_destroy(
    state: dict,
    config: dict,
    keycloak_token: str,
    organization: bool,
    solution: bool,
    workspace: bool,
    webapp: bool,
) -> None:
    """Call the appropriate delete helpers for each resource flagged for destruction."""
    api_state = state["services"]["api"]
    org_id = api_state["organization_id"]

    if solution:
        api = get_solution_api_instance(config=config, keycloak_token=keycloak_token)
        delete_api_resource(api.delete_solution, "Solution", org_id, api_state["solution_id"], state, "solution_id")

    if workspace:
        _destroy_workspace_resources(state, config, keycloak_token, org_id)

    if organization:
        api = get_organization_api_instance(config=config, keycloak_token=keycloak_token)
        delete_api_resource(api.delete_organization, "Organization", None, org_id, state, "organization_id")

    if webapp:
        destroy_webapp(state)


def _is_full_destroy(state: dict) -> bool:
    """Return True when every tracked resource ID has been cleared from the state.

    A single populated ID means the destroy was partial and states must be kept.
    """
    svc = state.get("services", {})
    api_ids = svc.get("api", {})
    return (
        not api_ids.get("organization_id")
        and not api_ids.get("solution_id")
        and not api_ids.get("workspace_id")
        and not svc.get("webapp", {}).get("webapp_name", "")
        and not svc.get("postgres", {}).get("schema_name", "")
    )


def _cleanup_local_state(state: dict, full_destroy: bool) -> None:
    """Delete the local state file on a full destroy, or persist the updated state on a partial one."""
    if full_destroy:
        logger.info("  [dim]🗑 All resources cleared ! removing local state file...[/dim]")
        if not env.delete_state_in_local():
            logger.warning(
                "  [yellow]⚠[/yellow] Could not delete the local state file destroy succeeded but the file may need manual cleanup."
            )
    else:
        logger.info("  [dim]↻ Partial destroy ! persisting updated state locally...[/dim]")
        env.store_state_in_local(state=state)


def _cleanup_remote_state(state: dict, full_destroy: bool) -> None:
    """Delete the Kubernetes secret on a full destroy, or sync the updated state on a partial one.

    No-op when the state has no remote backend configured.
    """
    if not state.get("remote"):
        return

    if full_destroy:
        logger.info("  [dim]☁ All resources cleared ! removing remote state secret from Kubernetes...[/dim]")
        if not env.delete_state_in_kubernetes():
            logger.warning(
                "  [yellow]⚠[/yellow] Could not delete the remote state secret !"
                "destroy succeeded but the secret may need manual cleanup."
            )
    else:
        logger.info("  [dim]↻ Partial destroy ! syncing updated state to Kubernetes...[/dim]")
        env.store_state_in_kubernetes(state=state)


def _print_destruction_summary(state: dict) -> None:
    """Print the post-destroy summary table showing the final status of every resource."""
    echo(style("\n📋 Destruction Summary", bold=True, fg="white"))

    services = state.get("services", {})
    api_data = services.get("api", {})
    for key, value in api_data.items():
        label_text = f"  • {key.replace('_', ' ').title()}"
        status = "DELETED" if not value else value
        color = "red" if status == "DELETED" else "green"
        echo(f"{style(f'{label_text:<20}:', fg='cyan', bold=True)} {style(status, fg=color)}")

    webapp_id = services.get("webapp", {}).get("webapp_name")
    label_text = "  • Webapp Name"
    status = "DELETED" if not webapp_id else webapp_id
    color = "red" if status == "DELETED" else "green"
    echo(f"{style(f'{label_text:<20}:', fg='cyan', bold=True)} {style(status, fg=color)}")

    echo(style("\n✨ Cleanup process complete", fg="white", bold=True))


@command()
@injectcontext()
@retrieve_state
@option("--include", "include", multiple=True, type=str, help="Specify the resources to destroy.")
@option("--exclude", "exclude", multiple=True, type=str, help="Specify the resources to exclude from destruction.")
@option("--yes", "-y", is_flag=True, default=False, help="Skip the interactive confirmation prompt.")
def destroy(state: dict, include: tuple[str, ...], exclude: tuple[str, ...], yes: bool):
    """Macro Destroy"""
    organization, solution, workspace, webapp = resolve_inclusion_exclusion(include, exclude)

    targeted = _build_targeted_resources(state, organization, solution, workspace, webapp)

    if not _confirm_destroy(include, exclude, targeted, yes=yes):
        echo()
        echo(style("  ✓ Deletion cancelled ! no resources were deleted.", fg="green", bold=True))
        echo()
        return CommandResponse.success()

    echo(style(f"\n🔥 Starting Destruction Process in namespace: {env.environ_id}", bold=True, fg="red"))
    keycloak_token, config = get_keycloak_token()

    _execute_destroy(state, config, keycloak_token, organization, solution, workspace, webapp)

    full_destroy = _is_full_destroy(state)
    _cleanup_local_state(state, full_destroy)
    _cleanup_remote_state(state, full_destroy)

    _print_destruction_summary(state)
    return CommandResponse.success()

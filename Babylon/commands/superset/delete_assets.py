from logging import getLogger

from click import command, echo, option, style

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
@option(
    "--wid",
    "workspace_id",
    required=True,
    type=str,
    default=None,
    help="Workspace ID used as the title prefix to identify assets (e.g. w-abc123)."
)
def delete_assets(state: dict, workspace_id: str | None) -> CommandResponse:
    """Delete all Superset dashboards, charts and datasets whose title starts with [workspace-id].

    Assets are deleted in dependency order: dashboards → charts → datasets.
    """

    if not workspace_id:
        logger.error("  [bold red]✘[/bold red] The --workspace-id option is required! Please provide a valid workspace ID.")
        return CommandResponse.fail()

    _, config = get_keycloak_token()

    superset_url = (config.get("superset_url") or "").rstrip("/")
    if not superset_url:
        logger.error("  [bold red]✘[/bold red] superset_url is not configured in the Kubernetes secret")
        return CommandResponse.fail()

    echo(style(f"🔥 Deleting Superset assets for workspace: {workspace_id}", bold=True, fg="yellow"))

    ok = delete_superset_assets(
        base_url=superset_url,
        superset_config=config,
        workspace_id=workspace_id,
    )

    if not ok:
        echo(style("⚠  Some assets could not be deleted — check the logs above.", fg="yellow"))
        return CommandResponse.fail()

    echo(style("✨ Superset asset cleanup complete.", fg="green", bold=True))
    return CommandResponse.success()

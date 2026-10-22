from logging import getLogger
from pathlib import Path as PathlibPath

from click import ClickException, command, confirm, echo, option, style
from click import Path as ClickPath

from Babylon.commands.api.workspace import get_workspace_api_instance
from Babylon.commands.macro.helpers.common import validate_inclusion_exclusion
from Babylon.commands.macro.helpers.workspace import (
    delete_api_resource,
    delete_kubernetes_resources,
    destroy_postgres_schema,
)
from Babylon.commands.macro.helpers.workspace.superset_helper import destroy_dashboard_assets
from Babylon.core.destroy import DestroyTarget
from Babylon.core.errors import InvalidOptionsError
from Babylon.core.models import DestroyOptions, ResourceStatus
from Babylon.core.operations import destroy as core_destroy
from Babylon.utils.decorators import injectcontext
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)
env = Environment()


def _build_targeted_resources(plan: list[DestroyTarget]) -> list[tuple[str, str]]:
    """(label, current-ID) pairs shown in the confirmation banner."""
    return [(t.label, t.resource_id or "(NOT DEPLOYED)") for t in plan]


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
    """Display the destruction warning banner and prompt the user for confirmation."""
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
        if label.lower() == "workspace":
            echo(
                style(
                    "        ↳ Note: This will also destroy all sidecar resources (PowerBI, Superset, Secrets, ConfigMap...)",
                    fg="bright_black",
                    italic=True,
                )
            )
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
    dataviz provider assets (Superset or Power BI), and the Workspace API object."""
    api_state = state["services"]["api"]
    schema_state = state["services"]["postgres"]

    # The provider is persisted at deploy time so the correct host/identities
    # (in-cluster for Superset, external Azure PostgreSQL for Power BI) are
    # used for teardown.
    provider = (schema_state.get("provider") or "powerbi").strip().lower()

    destroy_postgres_schema(schema_state["schema_name"], state, provider=provider)
    state["services"]["postgres"]["provider"] = ""
    delete_kubernetes_resources(
        namespace=env.environ_id,
        organization_id=org_id,
        workspace_id=api_state["workspace_id"],
    )

    if not destroy_dashboard_assets(provider, state, config):
        logger.warning(f"  [yellow]⚠[/yellow] Dataviz ('{provider}') asset cleanup was not fully successful")

    api = get_workspace_api_instance(config=config, keycloak_token=keycloak_token)
    delete_api_resource(api.delete_workspace, "Workspace", org_id, api_state["workspace_id"], state, "workspace_id")


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


@command()
@injectcontext()
@option(
    "--var-file",
    "variables_files",
    type=ClickPath(file_okay=True, exists=True, path_type=PathlibPath),
    default=["./variables.yaml"],
    multiple=True,
    help="Specify the path of your variable file. By default, it takes the variables.yaml file.",
)
@option("--include", "include", multiple=True, type=str, help="Specify the resources to destroy.")
@option("--exclude", "exclude", multiple=True, type=str, help="Specify the resources to exclude from destruction.")
@option("--yes", "-y", is_flag=True, default=False, help="Skip the interactive confirmation prompt.")
def destroy(variables_files: tuple, include: tuple[str, ...], exclude: tuple[str, ...], yes: bool):
    """Macro Destroy"""
    validate_inclusion_exclusion(include, exclude)  # same CLI messages as before (click.Abort)

    def ask(plan: list[DestroyTarget]) -> bool:
        """Banner + prompt, called by the core once the plan is known (before any deletion)."""
        if not _confirm_destroy(include, exclude, _build_targeted_resources(plan), yes=yes):
            return False
        echo(style(f"\n🔥 Starting Destruction Process in namespace: {env.environ_id}", bold=True, fg="red"))
        return True

    try:
        result = core_destroy(
            DestroyOptions(
                context=env.context_id,
                tenant=env.environ_id,
                variable_files=tuple(variables_files),
                include=tuple(include),
                exclude=tuple(exclude),
            ),
            confirm=ask,
        )
    except InvalidOptionsError as exc:
        raise ClickException(str(exc)) from None

    if result.nothing_to_destroy:
        echo()
        echo(
            style(
                f"  ✓ Nothing to destroy ! no deployed resource found in state-{env.context_id}-{env.environ_id}.",
                fg="green",
                bold=True,
            )
        )
        echo()
        return CommandResponse.success()

    if result.cancelled:
        echo()
        echo(style("  ✓ Deletion cancelled ! no resources were deleted.", fg="green", bold=True))
        echo()
        return CommandResponse.success()

    _print_destruction_summary(result.state)

    failed = [r for r in result.resources if r.status == ResourceStatus.FAILED]
    if failed:
        for r in failed:
            logger.error(f"  [bold red]✘[/bold red] {r.resource} {r.resource_id}: {r.error}")
        for r in result.resources:
            if r.status == ResourceStatus.SKIPPED and r.error == "previous resource failed":
                logger.warning(f"  [yellow]⚠[/yellow] {r.resource} {r.resource_id}: skipped, {r.error}")
        raise ClickException(f"{len(failed)} resource(s) failed to destroy")  # exit code 1
    echo(style("\n✨ Cleanup process complete", fg="white", bold=True))
    return CommandResponse.success()

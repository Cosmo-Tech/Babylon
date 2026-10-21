from logging import getLogger
from pathlib import Path as PathlibPath

from click import ClickException, argument, command, echo, option, style
from click import Path as ClickPath

from Babylon.commands.macro.helpers.common import validate_inclusion_exclusion
from Babylon.core.errors import InvalidOptionsError
from Babylon.core.models import ApplyOptions, ResourceStatus
from Babylon.core.operations import apply as core_apply
from Babylon.utils.decorators import injectcontext
from Babylon.utils.environment import Environment

logger = getLogger(__name__)
env = Environment()


def print_section(data: dict, highlight_urls: bool = False):
    for key, value in data.items():
        if not value:
            continue
        label = f"  • {key.replace('_', ' ').title()}"
        styled_label = style(f"{label:<20}:", fg="cyan", bold=True)

        if highlight_urls and "url" in key.lower():
            styled_value = style(str(value).strip(), fg="bright_blue", underline=True)
        else:
            styled_value = style(str(value).strip(), fg="white")

        echo(f"{styled_label} {styled_value}")


@command()
@injectcontext()
@argument("deploy_dir", type=ClickPath(dir_okay=True, exists=True, path_type=PathlibPath))
@option(
    "--var-file",
    "variables_files",
    type=ClickPath(file_okay=True, exists=True, path_type=PathlibPath),
    default=["./variables.yaml"],
    multiple=True,
    help="Specify the path of your variable file. By default, it takes the variables.yaml file.",
)
@option("--include", "include", multiple=True, type=str, help="Specify the resources to deploy.")
@option("--exclude", "exclude", multiple=True, type=str, help="Specify the resources to exclude from deployment.")
def apply(
    deploy_dir: PathlibPath,
    include: tuple[str, ...],
    exclude: tuple[str, ...],
    variables_files: tuple[PathlibPath, ...],
):
    """Macro Apply"""
    validate_inclusion_exclusion(include, exclude)  # same CLI messages as before (click.Abort)
    try:
        result = core_apply(
            ApplyOptions(
                deploy_dir=deploy_dir,
                context=env.context_id,
                tenant=env.environ_id,
                variable_files=tuple(variables_files),
                include=tuple(include),
                exclude=tuple(exclude),
            )
        )
    except InvalidOptionsError as exc:
        # click only formats its own exceptions ("Error: ..."); translate the core one.
        raise ClickException(str(exc)) from None
    final_state = env.get_state_from_local()
    services = final_state.get("services", {})
    api_data = services.get("api", {})
    webapp_data = services.get("webapp", {})
    echo(style("\n📋 Deployment Summary", bold=True, fg="yellow"))
    print_section(api_data)
    print_section(webapp_data)

    failed = [r for r in result.resources if r.status == ResourceStatus.FAILED]
    if failed:
        for r in failed:
            logger.error(f"  [bold red]✘[/bold red] {r.file} ({r.resource}): {r.error}")
        for r in result.resources:
            if r.status == ResourceStatus.SKIPPED:
                logger.warning(f"  [yellow]⚠[/yellow] {r.file} ({r.resource}): skipped, {r.error}")
        raise ClickException(f"{len(failed)} resource(s) failed to deploy")  # exit code 1
    echo(style("\n✨ Deployment process complete", fg="white", bold=True))
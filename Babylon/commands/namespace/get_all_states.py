from logging import getLogger

from click import Choice, argument, command, echo, style

from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)
env = Environment()


def _get_local_states() -> bool:
    echo(style("\n 📂 Local States", bold=True, fg="cyan"))
    if not env.state_dir.exists():
        logger.error(f"  [bold red]✘[/bold red] Directory not found: [dim]{env.state_dir}[/dim]")
        return False
    local_files = sorted(env.state_dir.glob("state.*.yaml"))
    if not local_files:
        logger.warning("  [yellow]⚠[/yellow] No local state files found")
        return False
    for f in local_files:
        echo(style("  • ", fg="green") + f.name)
    return True


def _get_remote_states() -> bool:
    echo(style("\n ☁️  Remote States", bold=True, fg="cyan"))
    try:
        remote_files = env.list_remote_states()
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Failed to reach remote storage: {e}")
        return False
    if not remote_files:
        logger.warning("  [yellow]⚠[/yellow] No remote states found")
        return False
    for name in sorted(remote_files):
        echo(style("  • ", fg="green") + name)
    return True


@command()
@argument("target", type=Choice(["local", "remote"], case_sensitive=False))
def get_states(target: str) -> CommandResponse:
    """Display states from local machine or remote Kubernetes storage."""
    handlers = {"local": _get_local_states, "remote": _get_remote_states}
    results_found = handlers[target]()
    return CommandResponse.success() if results_found else CommandResponse.fail()

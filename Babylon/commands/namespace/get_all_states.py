from logging import getLogger

from click import command, argument, Choice, echo, style

from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)
env = Environment()


@command()
@argument("target", type=Choice(["local", "remote"], case_sensitive=False))
def get_states(target: str) -> CommandResponse:
    """Display states from local machine or Azure remote storage."""
    
    results_found = False
    if target == "local":
        echo(style("\n 📂 Local States", bold=True, fg="cyan"))
        states_dir = env.state_dir
        
        if not states_dir.exists():
            logger.error(f"  [bold red]✘[/bold red] Directory not found: [dim]{states_dir}[/dim]")
        else:
            local_files = sorted(states_dir.glob("state.*.yaml"))
            if not local_files:
                logger.warning("  [yellow]⚠[/yellow] No local state files found")
            else:
                for f in local_files:
                    echo(style("  • ", fg="green") + f.name)
                    results_found = True
                    
    elif target == "remote":
        echo(style("\n ☁️  Remote States", bold=True, fg="cyan"))
        try:
            remote_files = env.list_remote_states()
            if not remote_files:
                logger.warning("  [yellow]⚠[/yellow] No remote states found on Azure")
            else:
                for name in sorted(remote_files):
                    echo(style("  • ", fg="green") + name)
                    results_found = True
        except Exception as e:
            logger.error(f"  [bold red]✘[/bold red] Failed to reach Azure storage: {e}")

    return CommandResponse.success() if results_found else CommandResponse.fail()
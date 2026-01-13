from logging import getLogger

from click import command

from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)
env = Environment()


@command()
def get_states() -> CommandResponse:
    """Display all states in your local machine"""
    states_dir = env.state_dir
    if not env.state_dir.exists():
        logger.error(f"directory {env.state_dir} not found")
        return CommandResponse.fail()
    states_files = sorted(states_dir.glob("state.*.yaml"))
    for f in states_files:
        print(f" {f.name}")
    return CommandResponse.success()

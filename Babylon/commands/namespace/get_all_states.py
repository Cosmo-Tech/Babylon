from logging import getLogger
from click import command
from Babylon.utils.response import CommandResponse
from Babylon.utils.environment import Environment

logger = getLogger("Babylon")
env = Environment()


@command()
def get_states() -> CommandResponse:
    """Display all states in your local machine"""
    states_dir = env.get_all_states_from_local()
    states_files = sorted(states_dir.glob("state.*.yaml"))
    for f in states_files:
        logger.info(f" {f.name}")
    return CommandResponse.success()

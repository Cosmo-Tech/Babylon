from logging import getLogger

from click import command

from Babylon.utils.decorators import wrapcontext
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)
env = Environment()


@command()
@wrapcontext()
def use() -> CommandResponse:
    """Switch to a specific Babylon namespace or create a new one"""
    env.store_namespace_in_local()
    logger.info(
        f"  [green]✔[/green] Switched to context [green]{env.context_id}[/green], tenant [green]{env.environ_id}[/green] successfully",
    )
    return CommandResponse.success()

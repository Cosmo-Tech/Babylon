from logging import getLogger
from click import command
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import wrapcontext
from Babylon.utils.environment import Environment

logger = getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
def use() -> CommandResponse:
    """Switch to a specific namespace or create a new one"""
    env.store_namespace_in_local()
    logger.info(f"[namespace] switched to context {[env.context_id]}, tenant {[env.environ_id]} successfully")
    return CommandResponse.success()

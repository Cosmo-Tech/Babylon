from logging import getLogger
from click import command
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.decorators import wrapcontext
from Babylon.utils.environment import Environment

logger = getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@timing_decorator
def use() -> CommandResponse:
    env.store_namespace_in_local()
    logger.info(f"Switched to namespace {env.context_id}, {env.environ_id} successfully.")
    return CommandResponse.success()

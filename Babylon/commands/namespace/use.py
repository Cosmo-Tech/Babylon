from logging import getLogger
from click import command
from Babylon.utils.response import CommandResponse
<<<<<<< HEAD
from Babylon.utils.decorators import timing_decorator, wrapcontext
=======
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.decorators import injectcontext
>>>>>>> 53b0a6f8 (add injectcontext)
from Babylon.utils.environment import Environment

logger = getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@timing_decorator
def use() -> CommandResponse:
    env.store_namespace_in_local()
    logger.info(f"Switched to namespace {env.context_id}, {env.environ_id} successfully")
    return CommandResponse.success()

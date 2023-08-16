import logging
import shutil

from click import command
from Babylon.utils.decorators import wrapcontext
from Babylon.utils.environment import Environment
from Babylon.utils.messages import SUCCESS_PAYLOAD_CREATED
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext
def create() -> CommandResponse:
    """
    Create a new solution payload
    """
    init_file = env.working_dir.original_template_path / "api/solution.yaml"
    target_file = env.working_dir.payload_path / f"{env.context_id}.{env.environ_id}.solution.yaml"
    shutil.copyfile(init_file, target_file)
    logger.info(SUCCESS_PAYLOAD_CREATED("solution"))
    return CommandResponse.success()

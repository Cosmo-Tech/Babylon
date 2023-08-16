import logging
import shutil

from click import Choice, command, option
from Babylon.utils.decorators import wrapcontext
from Babylon.utils.environment import Environment
from Babylon.utils.messages import SUCCESS_PAYLOAD_CREATED
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext
@option("--type", "type", type=Choice(['adt', 'storage']), required=True, help="Dataset type Cosmotech Platform")
def create(type: str) -> CommandResponse:
    """
    Create a new dataset payload
    """
    init_file = env.working_dir.original_template_path / f"api/dataset.{type}.yaml"
    target_file = env.working_dir.payload_path / f"{env.context_id}.{env.environ_id}.dataset.{type}.yaml"
    shutil.copyfile(init_file, target_file)
    logger.info(SUCCESS_PAYLOAD_CREATED("dataset"))
    return CommandResponse.success()

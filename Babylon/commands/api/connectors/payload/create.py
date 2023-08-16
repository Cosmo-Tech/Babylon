import logging
import shutil

from click import Choice, command, option
from Babylon.utils.environment import Environment
from Babylon.utils.messages import SUCCESS_PAYLOAD_CREATED
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@option("-t", "--type", "type", type=Choice(['adt', 'storage', 'twin']), required=True)
def create(type: str) -> CommandResponse:
    init_file = env.working_dir.original_template_path / f"api/connector.{type}.yaml"
    target_file = env.working_dir.payload_path / f"{env.context_id}.{env.environ_id}.connector.{type}.yaml"
    shutil.copyfile(init_file, target_file)
    logger.info(SUCCESS_PAYLOAD_CREATED("connector"))
    return CommandResponse.success()

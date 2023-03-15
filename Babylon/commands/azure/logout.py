import logging

from click import command
from click import confirm
from click import option

from ...utils.environment import Environment
from ...utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@option(
    "-f",
    "--force",
    "force_validation",
    is_flag=True,
    help="Don't ask for validation before delete",
)
def logout(force_validation: bool = False) -> CommandResponse:
    """Login to azure using secrets stored in .secrets.yaml"""
    if not force_validation and not confirm("You are trying to delete azure credentials from memory"
                                            "\nDo you want to continue ?"):
        return CommandResponse.fail()
    env = Environment()
    env.working_dir.set_encrypted_yaml_key(".secrets.yaml.encrypt", "azure", {})
    logger.info("Successfully deleted azure credentials")
    return CommandResponse.success()

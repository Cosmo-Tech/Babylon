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
    """Logout from Terraform Cloud using secrets stored in .secrets.yaml"""
    if not force_validation and not confirm("You are trying to delete tfc credentials from memory"
                                            "\nDo you want to continue ?"):
        return CommandResponse.fail()
    env = Environment()
    env.working_dir.set_encrypted_yaml_key(".secrets.yaml.encrypt", "tfc", {})
    logger.info("Successfully deleted tfc credentials")
    return CommandResponse.success()

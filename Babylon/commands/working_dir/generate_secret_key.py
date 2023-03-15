import logging
import pathlib

from click import command
from click import option
from click import confirm

from ...utils.environment import Environment
from ...utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@option("-o", "--override", "override", is_flag=True, help="Should override existing secret key")
def generate_secret_key(override: bool = False) -> CommandResponse:
    """Generates a new secret key"""
    wd = Environment().working_dir
    if override and not confirm("Are you sure you want to override existing secret key?", abort=True):
        return CommandResponse.fail()
    if not override and pathlib.Path(".secret.key").exists():
        logger.error("Secret key already exists. Use -o to override")
        return CommandResponse.fail()
    secret_path = wd.generate_secret_key(override=override)
    logger.info(f"Successfully generated secret key in {secret_path}")
    return CommandResponse.success()

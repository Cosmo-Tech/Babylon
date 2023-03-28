import logging

from click import command
from ...utils.response import CommandResponse
from ...utils.environment import Environment

logger = logging.getLogger("Babylon")


@command()
def init() -> CommandResponse:
    """
    Initialize Babylon configuration, working directory and secret key
    """
    env = Environment()
    logger.info("Configuration...")
    env.configuration.initialize()
    logger.info("Working directory...")
    env.working_dir.compare_to_template(update_if_error=True)
    logger.info("Secret key...")
    env.working_dir.generate_secret_key()
    logger.info("Successfully initialized Babylon configuration")
    return CommandResponse.success()

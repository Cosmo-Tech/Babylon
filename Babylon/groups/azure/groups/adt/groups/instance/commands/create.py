from click import command

import logging

logger = logging.getLogger("Babylon")


@command()
def create():
    """Command created from a template"""
    logger.warning("This command was initialized from a template and is empty")

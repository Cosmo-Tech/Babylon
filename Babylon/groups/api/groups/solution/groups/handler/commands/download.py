import logging

from click import command

logger = logging.getLogger("Babylon")


@command()
def download():
    """Command created from a template"""
    logger.warning("This command was initialized from a template and is empty")

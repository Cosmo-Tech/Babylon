from click import command

import logging

logger = logging.getLogger("Babylon")


@command()
def delete():
    """Command created from a template"""
    raise NotImplementedError("This command was initialized from a template and is empty")

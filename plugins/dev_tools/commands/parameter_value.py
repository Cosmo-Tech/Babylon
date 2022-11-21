import logging

from click import command
from click import argument

from rich.pretty import pretty_repr

from Babylon.utils.typing import QueryType

logger = logging.getLogger("Babylon")


@command()
@argument('arg', type=QueryType())
def parameter_value(arg):
    """Will display the value of the given QueryType argument"""
    logger.info("The value after conversion of the argument is:")
    logger.info(pretty_repr(arg))

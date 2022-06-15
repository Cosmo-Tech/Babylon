from click import command
from click import pass_obj
from click import argument

from ....utils.decorators import timing_decorator

from pathlib import Path
import logging

logger = logging.getLogger("Babylon")


@command()
@argument("filename")
@pass_obj
@timing_decorator
def connector(environment, filename):
    """Create a new connector in the API using FILENAME as a template"""
    file_path = Path(filename)
    if not file_path.is_file():
        logger.error(f"{filename} does not exists")
        return

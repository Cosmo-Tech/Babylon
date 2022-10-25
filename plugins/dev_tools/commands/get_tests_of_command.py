import logging

from click import argument
from click import command

from Babylon.utils import BABYLON_PATH

logger = logging.getLogger("Babylon")


@command()
@argument("command", nargs=-1)
def get_tests_of_command(command: list[str]):
    """Will go through the test organization to display the tests of the given COMMAND"""
    p = BABYLON_PATH.parent / ("tests/commands/" + "/".join(command))
    if p.exists():
        logger.info(f"Test of command {' '.join(command)}")
        with p.open("r") as f:
            for line in f:
                logger.info("  " + line)
    else:
        logger.info(f"Command {' '.join(command)} has no tests defined")

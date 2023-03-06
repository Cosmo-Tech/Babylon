import logging

import click
import rich.markdown
import rich

from Babylon.utils import BABYLON_PATH

logger = logging.getLogger("Babylon")


@click.command()
@click.argument("command", nargs=-1)
def how_to(command: list[str]):
    """Will go through the test organization to display the tests of the given COMMAND"""
    p = BABYLON_PATH.parent / ("tests/commands/" + "/".join(command))
    _c = rich.get_console()
    if not p.exists():
        logger.info(f"Command {' '.join(command)} has no tests defined")
        return
    logger.info(f"Test of command {' '.join(command)}")

    with p.open("r") as f:
        _c.print(rich.markdown.Markdown("".join(f.readlines())))

import logging
import pathlib
from typing import Optional

from click import command
from click import argument
from click import Path
from click import option

from ...utils.environment import Environment
from ...utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@argument("template_file", type=Path(path_type=pathlib.Path, dir_okay=False, exists=True))
@option("-o", "--output", "output_file", type=Path(path_type=pathlib.Path, dir_okay=False))
def fill_template(template_file: pathlib.Path, output_file: Optional[pathlib.Path]) -> CommandResponse:
    """Display current config"""
    data = Environment().fill_template(template_file)
    logger.info(data)
    if not output_file:
        return CommandResponse.success()
    with output_file.open("w") as f:
        f.write(str(data))
    return CommandResponse.success()

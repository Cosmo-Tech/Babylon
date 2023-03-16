import pathlib
import logging

from click import command
from click import argument
from click import Path
from click import option

from ...utils.environment import Environment
from ...utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@argument("template_path", type=Path(path_type=pathlib.Path, exists=True, dir_okay=False))
@option("-o",
        "--output",
        "output_file",
        type=Path(path_type=pathlib.Path, dir_okay=False),
        help="File to which content should be outputted")
def fill_template(template_path: pathlib.Path, output_file) -> CommandResponse:
    env = Environment()
    filled_tpl = env.fill_template(template_path)
    logger.info(filled_tpl)
    if output_file:
        with output_file.open("w") as f:
            f.write(str(filled_tpl))
    return CommandResponse.success()

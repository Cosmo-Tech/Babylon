import pathlib
import logging
from typing import Optional

from click import command
from click import argument
from click import Path
from click import option

from ...utils.environment import Environment
from ...utils.response import CommandResponse
from ...utils.typing import QueryType

logger = logging.getLogger("Babylon")


@command()
@argument("template_path", type=Path(path_type=Patth(exists=True, file_okay=True, dir_okay=False, readable=True, path_type=pathlib.Path), exists=True, dir_okay=False))
@option("-p", "--parameter", "params", type=(QueryType(), QueryType()), multiple=True)
@option("-o",
        "--output",
        "output_file",
        type=Path(path_type=Patth(exists=True, file_okay=True, dir_okay=False, readable=True, path_type=pathlib.Path), dir_okay=False),
        help="File to which content should be outputted")
def fill_template(template_path: pathlib.Path,
                  params: list[tuple[str, str]] = [],
                  output_file: Optional[pathlib.Path] = None) -> CommandResponse:
    env = Environment()
    data = {param[0]: param[1] for param in params}
    filled_tpl = env.fill_template(template_path, data)
    logger.info(filled_tpl)
    if output_file:
        with output_file.open("w") as f:
            f.write(str(filled_tpl))
    return CommandResponse.success()

import logging
import pathlib
from typing import Optional

from click import command
from click import option
from click import Path

from ....utils.environment import Environment
from ....utils.response import CommandResponse

logger = logging.getLogger("Babylon")

DEFAULT_WEBAPP_TEMPLATE = "templates/webapp_config.tpl.env"


@command()
@option("-o",
        "--output",
        "output_file",
        help="File to which content should be outputted (json-formatted)",
        required=True)
@option("-t", "--template", "template_file", type=Path(readable=True, dir_okay=False, path_type=pathlib.Path))
@option("-e",
        "--use-working-dir-file",
        "use_working_dir_file",
        is_flag=True,
        help="Should the parameter file path be relative to Babylon working directory ?")
def export_environment(output_file: str,
                       template_file: Optional[str] = None,
                       use_working_dir_file: bool = False) -> CommandResponse:
    """Export data in a file given a template"""
    env = Environment()
    if not template_file:
        template_file = env.working_dir.get_file(DEFAULT_WEBAPP_TEMPLATE)
    elif use_working_dir_file:
        template_file = env.working_dir.get_file(str(template_file))
    filled = env.fill_template(template_file)
    with open(output_file, "w") as _file:
        _file.write(filled)
    return CommandResponse.success()

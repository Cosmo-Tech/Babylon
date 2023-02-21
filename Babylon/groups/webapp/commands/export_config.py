import logging
import pathlib
from typing import Optional
import json

from click import command
from click import option
from click import Path

from ....utils.environment import Environment
from ....utils.response import CommandResponse
from ....utils.decorators import output_to_file

logger = logging.getLogger("Babylon")

DEFAULT_PAYLOAD_TEMPLATE = ".payload_templates/webapp/webapp_config.json"


@command()
@option("-f", "--file", "template_file", type=Path(readable=True, dir_okay=False, path_type=pathlib.Path))
@option("-e",
        "--use-working-dir-file",
        "use_working_dir_file",
        is_flag=True,
        help="Should the output file path be relative to Babylon working directory ?")
@output_to_file
def export_config(template_file: Optional[pathlib.Path] = None, use_working_dir_file: bool = False) -> CommandResponse:
    """Export webapp configuration in a json file"""
    env = Environment()
    template_file = template_file or env.working_dir.get_file(DEFAULT_PAYLOAD_TEMPLATE)
    config_data = env.fill_template(template_file, use_working_dir_file=use_working_dir_file)
    return CommandResponse.success(json.loads(config_data))

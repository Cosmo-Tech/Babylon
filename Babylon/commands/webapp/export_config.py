import logging
import pathlib
from typing import Optional
import json

from click import command
from click import option
from click import Path

from ...utils.environment import Environment
from ...utils.response import CommandResponse
from ...utils.decorators import output_to_file

logger = logging.getLogger("Babylon")


@command()
@option("-f",
        "--file",
        "config_file",
        type=Path(readable=True,
                  dir_okay=False,
                  path_type=Path(exists=True, file_okay=True, dir_okay=False, readable=True, path_type=pathlib.Path)))
@output_to_file
def export_config(config_file: Optional[pathlib.Path] = None) -> CommandResponse:
    """Export webapp configuration in a json file"""
    env = Environment()
    config_file = config_file or env.working_dir.payload_path / "webapp/webapp_config.json"
    config_data = env.fill_template(config_file)
    return CommandResponse.success(json.loads(config_data))

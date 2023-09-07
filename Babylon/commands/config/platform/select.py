import logging
import pathlib

from click import argument
from click import command
from click import Path

from ....utils.environment import Environment
from ....utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@argument("platform", type=Path(path_type=Path(exists=True, file_okay=True, dir_okay=False, readable=True, path_type=pathlib.Path)))
def select(platform: pathlib.Path) -> CommandResponse:
    """Change active platform file in given platform"""
    config = Environment().configuration
    platform = platform.with_suffix(".yaml")
    if not platform.is_absolute():
        platform = config.config_dir / platform
    config.set_platform(platform)
    return CommandResponse.success()

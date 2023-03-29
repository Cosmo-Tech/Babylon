import logging
import pathlib

from click import argument
from click import command
from click import Path

from ....utils.environment import Environment
from ....utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@argument("deploy", type=Path(path_type=pathlib.Path))
def select(deploy: pathlib.Path) -> CommandResponse:
    """Change active deploy file in given platform"""
    config = Environment().configuration
    deploy = deploy.with_suffix(".yaml")
    if not deploy.is_absolute():
        deploy = config.config_dir / deploy
    config.set_deploy(deploy)
    return CommandResponse.success()

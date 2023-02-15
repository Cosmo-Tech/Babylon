import logging
import pathlib

from click import command
from click import option
from click import argument
from click import Path

from .....utils.request import oauth_request
from .....utils.response import CommandResponse
from .....utils.environment import Environment
from .....utils.credentials import pass_azure_token
from .....utils.typing import QueryType

logger = logging.getLogger("Babylon")


@command()
@pass_azure_token("graph")
@argument("registration_id", type=QueryType())
@option("-f",
        "--file",
        "registration_file",
        type=Path(readable=True, dir_okay=False, path_type=pathlib.Path),
        required=True)
@option("-e",
        "--use-working-dir-file",
        "use_working_dir_file",
        is_flag=True,
        help="Should the parameter file path be relative to Babylon working directory ?")
def update(azure_token: str,
           registration_id: str,
           registration_file: pathlib.Path,
           use_working_dir_file: bool = False) -> CommandResponse:
    """
    Update an app registration in active directory
    https://learn.microsoft.com/en-us/graph/api/application-update
    """
    route = f"https://graph.microsoft.com/v1.0/applications/{registration_id}"
    env = Environment()
    details = env.fill_template(registration_file, use_working_dir=use_working_dir_file)
    response = oauth_request(route, azure_token, type="PATCH", data=details)
    if response is None:
        return CommandResponse.fail()
    logger.info(f"Successfully updated registration {registration_id}")
    return CommandResponse.success()

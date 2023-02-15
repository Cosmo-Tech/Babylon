import logging
import pathlib

from click import command
from click import option
from click import Path
from rich.pretty import pretty_repr

from ........utils.request import oauth_request
from ........utils.response import CommandResponse
from ........utils.environment import Environment
from ........utils.decorators import output_to_file
from ........utils.credentials import get_azure_token

logger = logging.getLogger("Babylon")

DEFAULT_PAYLOAD_TEMPLATE = ".payload_templates/webapp/app_registration.json"


@command()
@option("-f",
        "--file",
        "registration_file",
        type=Path(readable=True, dir_okay=False, path_type=pathlib.Path))
@option("-e",
        "--use-working-dir-file",
        "use_working_dir_file",
        is_flag=True,
        help="Should the parameter file path be relative to Babylon working directory ?")
@output_to_file
def create(registration_file: pathlib.Path, use_working_dir_file: bool = False) -> CommandResponse:
    """
    Register an app in active directory
    https://learn.microsoft.com/en-us/graph/api/application-post-applications
    """
    route = "https://graph.microsoft.com/v1.0/applications"
    env = Environment()
    registration_file = registration_file or env.working_dir.get_file(DEFAULT_PAYLOAD_TEMPLATE)
    details = env.fill_template(registration_file, use_working_dir_file=use_working_dir_file)
    response = oauth_request(route, get_azure_token("graph"), type="POST", data=details)
    if response is None:
        return CommandResponse.fail()
    output_data = response.json()
    logger.info(pretty_repr(output_data))
    return CommandResponse.success(output_data)

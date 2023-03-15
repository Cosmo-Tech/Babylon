import logging
import pathlib

from click import command
from click import option
from click import Path
from click import argument
from rich.pretty import pretty_repr

from .....utils.request import oauth_request
from .....utils.response import CommandResponse
from .....utils.environment import Environment
from .....utils.decorators import output_to_file
from .....utils.credentials import pass_azure_token
from .....utils.typing import QueryType

logger = logging.getLogger("Babylon")


@command()
@pass_azure_token("graph")
@argument("name", type=QueryType())
@option("-f", "--file", "registration_file", type=Path(readable=True, dir_okay=False, path_type=pathlib.Path))
@output_to_file
def create(azure_token: str, name: str, registration_file: pathlib.Path) -> CommandResponse:
    """
    Register an app in active directory
    https://learn.microsoft.com/en-us/graph/api/application-post-applications
    """
    route = "https://graph.microsoft.com/v1.0/applications"
    env = Environment()
    payload_template = env.working_dir.payload_path / "webapp/app_registration.json"
    registration_file = registration_file or payload_template
    details = env.fill_template(registration_file, data={"app_name": name})
    response = oauth_request(route, azure_token, type="POST", data=details)
    if response is None:
        return CommandResponse.fail()
    output_data = response.json()
    logger.info(pretty_repr(output_data))
    return CommandResponse.success(output_data)

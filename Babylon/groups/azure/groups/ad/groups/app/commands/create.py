import logging
import pathlib
from string import Template

from azure.core.credentials import AccessToken
from click import command
from click import pass_context
from click import Context
from click import option
from click import Path
from rich.pretty import pretty_repr

from ........utils.request import oauth_request
from ........utils.response import CommandResponse
from ........utils.environment import Environment
from ........utils.decorators import output_to_file

logger = logging.getLogger("Babylon")


@command()
@pass_context
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
@output_to_file
def create(ctx: Context, registration_file: str, use_working_dir_file: bool = False) -> CommandResponse:
    """
    Register an app in active directory
    https://learn.microsoft.com/en-us/graph/api/application-post-applications
    """
    access_token = ctx.find_object(AccessToken).token
    route = "https://graph.microsoft.com/v1.0/applications"
    env = Environment()
    if use_working_dir_file:
        registration_file = env.working_dir.get_file(str(registration_file))
    details = ""
    with open(registration_file, "r") as _file:
        template = _file.read()
        data = {**env.configuration.get_deploy(), **env.configuration.get_platform()}
        try:
            details = Template(template).substitute(data)
        except Exception as e:
            logger.error(f"Could not fill parameters template: {e}")
            return CommandResponse.fail()
    response = oauth_request(route, access_token, type="POST", data=details)
    if response is None:
        return CommandResponse.fail()
    output_data = response.json()
    logger.info(pretty_repr(output_data))
    return CommandResponse.success(output_data)

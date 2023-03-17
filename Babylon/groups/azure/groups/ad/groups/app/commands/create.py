import logging
import pathlib

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

DEFAULT_PAYLOAD_TEMPLATE = ".payload_templates/webapp/app_registration.json"


@command()
@pass_context
@option("-f", "--file", "registration_file", type=Path(readable=True, dir_okay=False, path_type=pathlib.Path))
@option("-e",
        "--use-working-dir-file",
        "use_working_dir_file",
        is_flag=True,
        help="Should the parameter file path be relative to Babylon working directory ?")
@output_to_file
def create(ctx: Context, registration_file: pathlib.Path, use_working_dir_file: bool = False) -> CommandResponse:
    """
    Register an app in active directory
    https://learn.microsoft.com/en-us/graph/api/application-post-applications
    """
    access_token = ctx.find_object(AccessToken).token
    route = "https://graph.microsoft.com/v1.0/applications"
    env = Environment()
    registration_file = registration_file or env.working_dir.get_file(DEFAULT_PAYLOAD_TEMPLATE)
    details = env.fill_template(registration_file, use_working_dir_file=use_working_dir_file)
    response = oauth_request(route, access_token, type="POST", data=details)
    if response is None:
        return CommandResponse.fail()
    output_data = response.json()
    # Service principal creation
    sp_route = "https://graph.microsoft.com/v1.0/servicePrincipals"
    sp_response = oauth_request(sp_route, access_token, type="POST", json={"appId": output_data["appId"]})
    if sp_response is None:
        logger.error("Failed to create application service principal")
        return CommandResponse.fail()
    output_data["servicePrincipalId"] = sp_response.json()["id"]
    logger.info(pretty_repr(output_data))
    return CommandResponse.success(output_data)
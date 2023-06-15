import logging
import pathlib
import polling2

from click import command
from click import option
from click import Path
from click import argument

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
    
    handler = polling2.poll(
        lambda: oauth_request(route, azure_token, type="POST", data=details),
    check_success=is_correct_response_app,
    step=1,
    timeout=60)

    output_data = handler.json()

    # Service principal creation
    sp_route = "https://graph.microsoft.com/v1.0/servicePrincipals"

    sp_response = polling2.poll(
        lambda: oauth_request(sp_route, azure_token, type="POST", json={"appId": output_data['appId']}),
    check_success=is_correct_response_serviceprincipal,
    step=1,
    timeout=60)
    sp_response = sp_response.json()
    if sp_response is None:
        logger.error("Failed to create application service principal")
        return CommandResponse.fail()
    output_data["servicePrincipalId"] = sp_response["id"]
    return CommandResponse.success(output_data, verbose=True)

def is_correct_response_app(response):
    if response is None:
        return CommandResponse.fail()
    output_data = response.json()
    if "id" in output_data:
        return True

def is_correct_response_serviceprincipal(response):
    if response is None:
        return CommandResponse.fail()
    output_data = response.json()
    if "id" in output_data:
        return True
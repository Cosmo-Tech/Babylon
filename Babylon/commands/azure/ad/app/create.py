import logging
import pathlib
import polling2

from click import Context, command, pass_context
from click import option
from click import Path
from click import argument
from Babylon.utils.checkers import check_ascii
from Babylon.utils.messages import SUCCESS_CONFIG_UPDATED
from Babylon.utils.request import oauth_request
from Babylon.utils.response import CommandResponse
from Babylon.utils.environment import Environment
from Babylon.utils.decorators import output_to_file
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.typing import QueryType

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@pass_context
@output_to_file
@pass_azure_token("graph")
@option("-f", "--file", "registration_file", type=Path(readable=True, dir_okay=False, path_type=pathlib.Path))
@option("-s", "--select", "select", is_flag=True, default=True, help="Save this new organization in configuration")
@argument("name", type=QueryType())
def create(ctx: Context, azure_token: str, name: str, select: bool, registration_file: pathlib.Path) -> CommandResponse:
    """
    Register an app in Active Directory
    https://learn.microsoft.com/en-us/graph/api/application-post-applications
    """
    check_ascii(name)
    route = "https://graph.microsoft.com/v1.0/applications"
    registration_file = registration_file or env.working_dir.original_template_path / "webapp/app_registration.json"
    details = env.fill_template(registration_file, data={"app_name": name})

    handler = polling2.poll(lambda: oauth_request(route, azure_token, type="POST", data=details),
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
    if select:
        r_id = ctx.parent.command.name
        env.configuration.set_var(resource_id=r_id, var_name="app_id", var_value=sp_response["appId"])
        logger.info(SUCCESS_CONFIG_UPDATED("app", "app_id"))
        env.configuration.set_var(resource_id=r_id, var_name="name", var_value=sp_response["appDisplayName"])
        logger.info(SUCCESS_CONFIG_UPDATED("app", "name"))
        env.configuration.set_var(resource_id=r_id, var_name="principal_id", var_value=sp_response["id"])
        logger.info(SUCCESS_CONFIG_UPDATED("app", "principal_id"))
        env.configuration.set_var(resource_id=r_id, var_name="object_id", var_value=output_data["id"])
        logger.info(SUCCESS_CONFIG_UPDATED("app", "object_id"))
    return CommandResponse.success(sp_response, verbose=True)


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

import logging

from click import Context, command, pass_context
from click import argument
from click import option
from Babylon.utils.checkers import check_ascii
from Babylon.utils.decorators import output_to_file, wrapcontext
from Babylon.utils.messages import SUCCESS_CONFIG_UPDATED, SUCCESS_CREATED
from Babylon.utils.typing import QueryType
from Babylon.utils.response import CommandResponse
from Babylon.utils.request import oauth_request
from Babylon.utils.environment import Environment
from Babylon.utils.credentials import pass_powerbi_token

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@pass_context
@output_to_file
@pass_powerbi_token()
@option("--select", "select", is_flag=True, default=True, help="Select this new Workspace PowerBI")
@argument("name", type=QueryType())
def create(ctx: Context, powerbi_token: str, name: str, select: bool) -> CommandResponse:
    """
    Create workspace named WORKSPACE_NAME into Power Bi App
    """
    check_ascii(name)
    url_groups = 'https://api.powerbi.com/v1.0/myorg/groups?$workspaceV2=True'
    response = oauth_request(url=url_groups, access_token=powerbi_token, json={"name": name}, type="POST")
    if response is None:
        return CommandResponse.fail()
    output_data = response.json()
    if select:
        env.configuration.set_var(resource_id="powerbi", var_name=["workspace", "id"], var_value=output_data["id"])
        logger.info(SUCCESS_CONFIG_UPDATED("powerbi", "id"))
        env.configuration.set_var(resource_id="powerbi", var_name=["workspace", "name"], var_value=name)
        logger.info(SUCCESS_CONFIG_UPDATED("powerbi", "name"))
    logger.info(SUCCESS_CREATED("Workspace powerbi", output_data['id']))
    return CommandResponse.success(output_data, verbose=True)

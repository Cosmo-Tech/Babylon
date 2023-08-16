import logging

from typing import Any, Optional
from click import command
from click import option
from Babylon.utils.messages import SUCCESS_CONFIG_UPDATED
from Babylon.utils.response import CommandResponse
from Babylon.utils.environment import Environment
from Babylon.utils.typing import QueryType
from Babylon.utils.request import oauth_request
from Babylon.utils.credentials import pass_powerbi_token
from Babylon.utils.decorators import inject_context_with_resource

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@pass_powerbi_token()
@option("-w", "--workspace", "workspace_id", help="PowerBI workspace ID", type=QueryType())
@option("-n", "--name", "name", help="PowerBI workspace name", type=QueryType())
@option("-s", "--select", "select", is_flag=True, default=True, help="Select this workspace PowerBI")
@inject_context_with_resource({"powerbi": ['workspace']})
def get(
    context: Any,
    powerbi_token: str,
    select: bool,
    workspace_id: Optional[str] = None,
    name: Optional[str] = None,
) -> CommandResponse:
    """
    Get a specific workspace information
    """
    if not workspace_id:
        logger.info("You trying to use key : workspace id referenced in configuration")
    workspace_id = workspace_id or context['powerbi_workspace']['id']
    url_groups = 'https://api.powerbi.com/v1.0/myorg/groups'
    params = {"$filter": f"id eq '{workspace_id}'"} if workspace_id else {"$filter": f"name eq '{name}'"}
    response = oauth_request(url_groups, powerbi_token, params=params)
    if response is None:
        return CommandResponse.fail()
    workspace_data = response.json().get('value')
    if not workspace_data:
        logger.error(f"{name} not found")
        return CommandResponse.fail()
    if len(workspace_data) and select:
        workspace_id = workspace_data[0]['id']
        env.configuration.set_var(resource_id="powerbi", var_name=["workspace", "id"], var_value=workspace_id)
        logger.info(SUCCESS_CONFIG_UPDATED("workspace", "id"))
        env.configuration.set_var(resource_id="powerbi", var_name=["workspace", "name"], var_value=name)
        logger.info(SUCCESS_CONFIG_UPDATED("workspace", "name"))
    return CommandResponse.success(workspace_data[0], verbose=True)

import logging
from typing import Optional

from click import command
from click import option

from ....utils.response import CommandResponse
from ....utils.environment import Environment
from ....utils.typing import QueryType
from ....utils.request import oauth_request
from ....utils.credentials import pass_azure_token

logger = logging.getLogger("Babylon")


@command()
@pass_azure_token("powerbi")
@option("-w", "--workspace", "workspace_id", help="PowerBI workspace ID", type=QueryType())
@option("-n", "--name", "name", help="PowerBI workspace name", type=QueryType())
@option("-s",
        "--select",
        "select",
        is_flag=True,
        help="Select this workspace ?",
        default=False)
def get(azure_token: str,
        select: bool,
        workspace_id: Optional[str] = None, 
        name: Optional[str] = None,
    ) -> CommandResponse:
    """Get a specific workspace information"""
    if not workspace_id and not name:
        logger.error("A workspace id or name is required with parameter '-w' or '-n'")
        return CommandResponse.fail()
    url_groups = 'https://api.powerbi.com/v1.0/myorg/groups'
    params = {"$filter": f"id eq '{workspace_id}'"} if workspace_id else {"$filter": f"name eq '{name}'"}
    response = oauth_request(url_groups, azure_token, params=params)
    if response is None:
        return CommandResponse.fail()
    workspace_data = response.json().get('value')
    if not workspace_data:
        logger.error(f"{workspace_id} was not found")
        return CommandResponse.fail()
    if select:
        if len(workspace_data) == 1:
            workspace_id = workspace_data[0]['id']
        env = Environment()
        env.configuration.set_deploy_var("powerbi_workspace_id",workspace_id)
    return CommandResponse.success(workspace_data[0], verbose=True)

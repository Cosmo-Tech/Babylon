import logging
from typing import Optional

from azure.core.credentials import AccessToken
from click import Context
from click import command
from click import option
from click import pass_context

from ......utils.logging import table_repr
from ......utils.response import CommandResponse
from ......utils.typing import QueryType
from ......utils.request import oauth_request

logger = logging.getLogger("Babylon")


@command()
@pass_context
@option("-w", "--workspace", "workspace_id", help="PowerBI workspace ID", type=QueryType())
@option("-n", "--name", "name", help="PowerBI workspace name")
def get(ctx: Context, workspace_id: Optional[str] = None, name: Optional[str] = None) -> CommandResponse:
    """Get a specific workspace information"""
    if not workspace_id and not name:
        logger.error("A workspace id or name is required with parameter '-w' or '-n'")
        return CommandResponse.fail()
    url_groups = 'https://api.powerbi.com/v1.0/myorg/groups'
    access_token = ctx.find_object(AccessToken).token
    params = {"$filter": f"id eq '{workspace_id}'"} if workspace_id else {"$filter": f"name eq '{name}'"}
    response = oauth_request(url=url_groups, access_token=access_token, params=params)
    if response is None:
        return CommandResponse.fail()
    workspace_data = response.json().get('value')
    if not workspace_data:
        logger.error(f"{workspace_id} was not found")
        return CommandResponse.fail()
    logger.info("\n".join(table_repr(workspace_data)))
    return CommandResponse.success(workspace_data)

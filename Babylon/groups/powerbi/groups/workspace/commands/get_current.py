import logging

from azure.core.credentials import AccessToken
from click import Context
from click import command
from click import pass_context

from ......utils.decorators import require_deployment_key
from ......utils.logging import table_repr
from ......utils.response import CommandResponse
from ......utils.request import oauth_request

logger = logging.getLogger("Babylon")


@command()
@pass_context
@require_deployment_key("powerbi_workspace_id")
def get_current(ctx: Context, powerbi_workspace_id: str) -> CommandResponse:
    """Get a specific workspace information"""
    url_groups = 'https://api.powerbi.com/v1.0/myorg/groups'
    access_token = ctx.find_object(AccessToken).token
    params = {"$filter": f"id eq '{powerbi_workspace_id}'"}
    response = oauth_request(url=url_groups, access_token=access_token, params=params)
    if response is None:
        return CommandResponse.fail()
    workspace_data = response.json().get('value')
    if not workspace_data:
        logger.error(f"{powerbi_workspace_id} was not found")
        return CommandResponse.fail()
    logger.info("\n".join(table_repr(workspace_data)))
    return CommandResponse(data=workspace_data)

import logging

from click import command

from ......utils.decorators import require_deployment_key
from ......utils.logging import table_repr
from ......utils.response import CommandResponse
from ......utils.request import oauth_request
from ......utils.credentials import pass_azure_token

logger = logging.getLogger("Babylon")


@command()
@pass_azure_token("powerbi")
@require_deployment_key("powerbi_workspace_id")
def get_current(azure_token: str, powerbi_workspace_id: str) -> CommandResponse:
    """Get a specific workspace information"""
    url_groups = 'https://api.powerbi.com/v1.0/myorg/groups'
    params = {"$filter": f"id eq '{powerbi_workspace_id}'"}
    response = oauth_request(url_groups, azure_token, params=params)
    if response is None:
        return CommandResponse.fail()
    workspace_data = response.json().get('value')
    if not workspace_data:
        logger.error(f"{powerbi_workspace_id} was not found")
        return CommandResponse.fail()
    logger.info("\n".join(table_repr(workspace_data)))
    return CommandResponse(data=workspace_data)

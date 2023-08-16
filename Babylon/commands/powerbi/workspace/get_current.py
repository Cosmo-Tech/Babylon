import logging

from typing import Any
from click import command
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.response import CommandResponse
from Babylon.utils.request import oauth_request
from Babylon.utils.credentials import pass_powerbi_token

logger = logging.getLogger("Babylon")


@command()
@wrapcontext()
@pass_powerbi_token()
@inject_context_with_resource({"powerbi": ['workspace']})
def get_current(
    context: Any,
    powerbi_token: str,
) -> CommandResponse:
    """
    Get a specific workspace information
    """
    workspace_id = context['powerbi_workspace']['id']
    url_groups = 'https://api.powerbi.com/v1.0/myorg/groups'
    params = {"$filter": f"id eq '{workspace_id}'"}
    response = oauth_request(url_groups, powerbi_token, params=params)
    if response is None:
        return CommandResponse.fail()
    workspace_data = response.json().get('value')
    if not workspace_data:
        logger.error(f"{workspace_id} not found")
        return CommandResponse.fail()
    return CommandResponse(data=workspace_data, verbose=True)

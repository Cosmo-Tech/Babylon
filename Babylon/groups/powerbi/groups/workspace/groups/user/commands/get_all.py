import logging
from typing import Optional

from click import command
from click import option

from ........utils.decorators import require_deployment_key
from ........utils.decorators import output_to_file
from ........utils.logging import table_repr
from ........utils.typing import QueryType
from ........utils.response import CommandResponse
from ........utils.request import oauth_request
from ........utils.credentials import get_azure_token

logger = logging.getLogger("Babylon")


@command()
@option("-w", "--workspace", "override_workspace_id", type=QueryType())
@require_deployment_key("powerbi_workspace_id", required=False)
@output_to_file
def get_all(powerbi_workspace_id: str, override_workspace_id: Optional[str] = None) -> CommandResponse:
    """List all exisiting users in the power bi workspace"""
    workspace_id = override_workspace_id or powerbi_workspace_id
    if not workspace_id:
        logger.error("A workspace id is required either in your config or with parameter '-w'")
        return CommandResponse.fail()
    url_users = f'https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/users'
    response = oauth_request(url_users, get_azure_token("powerbi"))
    if response is None:
        return CommandResponse.fail()
    users = response.json().get('value')
    logger.info("\n".join(table_repr(users)))
    return CommandResponse.success(users)

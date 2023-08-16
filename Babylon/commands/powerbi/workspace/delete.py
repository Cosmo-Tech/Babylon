import logging

from typing import Any
from click import command
from click import option
from Babylon.utils.environment import Environment
from Babylon.utils.interactive import confirm_deletion
from Babylon.utils.messages import SUCCESS_DELETED
from Babylon.utils.typing import QueryType
from Babylon.utils.response import CommandResponse
from Babylon.utils.request import oauth_request
from Babylon.utils.credentials import pass_powerbi_token
from Babylon.utils.decorators import inject_context_with_resource

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@pass_powerbi_token()
@option("-D", "force_validation", is_flag=True, help="Delete on force mode")
@option("-w", "--workspace-id", "workspace_id", type=QueryType())
@inject_context_with_resource({"powerbi": ['workspace']})
def delete(context: Any, powerbi_token: str, workspace_id: str, force_validation: bool) -> CommandResponse:
    """
    Delete workspace from Power Bi APP
    """
    if not workspace_id:
        logger.warning(f"You trying to use workspace referenced in '{env.context_id}.{env.environ_id}.powerbi.yaml'")
        logger.warning(f"Current value: {context['powerbi_workspace']['id']}")
    workspace_id = workspace_id or context['powerbi_workspace']['id']
    if not force_validation and not confirm_deletion("Power Bi Workspace", workspace_id):
        return CommandResponse.fail()
    url_delete = f'https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}'
    response = oauth_request(url=url_delete, access_token=powerbi_token, type="DELETE")
    if response is None:
        return CommandResponse.fail()
    logger.info(SUCCESS_DELETED("PowerBI workspace", workspace_id))
    return CommandResponse.success()

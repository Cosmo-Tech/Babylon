from logging import getLogger
from typing import Any
from click import Context, command, pass_context
from click import argument
from click import option
from Babylon.utils.interactive import confirm_deletion
from Babylon.utils.decorators import inject_context_with_resource
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.request import oauth_request
from Babylon.utils.typing import QueryType

logger = getLogger("Babylon")
env = Environment()


@command()
@pass_context
@timing_decorator
@pass_azure_token("csm_api")
@option("-D", "force_validation", is_flag=True, help="Delete on force mode")
@argument("id", type=QueryType(), required=False)
@inject_context_with_resource({"api": ['url', 'organization_id']})
def delete(
    ctx: Context,
    context: Any,
    azure_token: str,
    id: str,
    force_validation: bool = False,
) -> CommandResponse:
    """
    Delete a workspace
    """
    workspace_id = env.configuration.get_var(resource_id=ctx.parent.parent.command.name, var_name="workspace_id")
    if not id:
        logger.error(f"You trying to {ctx.command.name} {ctx.parent.command.name} referenced in configuration")
        logger.error(f"Current value: {workspace_id}")
    if not workspace_id:
        logger.error("Workspace id is missing")
        return CommandResponse.fail()
    workspace_id = id or workspace_id
    if not force_validation and not confirm_deletion("workspace", workspace_id):
        return CommandResponse.fail()
    response = oauth_request(
        f"{context['api_url']}/organizations/{context['api_organization_id']}/workspaces/{workspace_id}",
        azure_token,
        type="DELETE")
    if response is None:
        return CommandResponse.fail()
    logger.info(f"Successfully deleted workspace {workspace_id} from organization {context['api_organization_id']}")
    return CommandResponse.success()

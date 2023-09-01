from logging import getLogger
from typing import Any
from click import Context, argument, command, option, pass_context
from Babylon.utils.typing import QueryType
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import inject_context_with_resource
from Babylon.utils.decorators import output_to_file
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.request import oauth_request
from Babylon.utils.response import CommandResponse
from Babylon.utils.environment import Environment

logger = getLogger("Babylon")
env = Environment()


@command()
@pass_context
@timing_decorator
@output_to_file
@pass_azure_token("csm_api")
@option("--select", "select", is_flag=True, default=True, help="Save this new organization in configuration")
@argument("id", type=QueryType(), required=False)
@inject_context_with_resource({"api": ['url', 'organization_id']})
def get(ctx: Context, context: Any, azure_token: str, id: str, select: bool) -> CommandResponse:
    """
    Get a workspace details
    """
    workspace_id = id or env.configuration.get_var(resource_id=ctx.parent.parent.command.name, var_name="workspace_id")
    if not id:
        logger.info(f"You trying to {ctx.command.name} {ctx.parent.command.name} referenced in configuration")
        logger.info(f"Current value: {workspace_id}")
    if not workspace_id:
        logger.info("Workspace id is missing")
        return CommandResponse.fail()
    response = oauth_request(
        f"{context['api_url']}/organizations/{context['api_organization_id']}/workspaces/{workspace_id}", azure_token)
    if response is None:
        return CommandResponse.fail()
    workspace = response.json()
    if select:
        env.configuration.set_var(resource_id=ctx.parent.parent.command.name,
                                  var_name="workspace_id",
                                  var_value=workspace["id"])
        logger.info("Updated configuration variables")
    return CommandResponse.success(workspace, verbose=True)

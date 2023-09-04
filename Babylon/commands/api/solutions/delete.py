from logging import getLogger
from typing import Any
from click import Context, argument, pass_context
from click import command
from click import option
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.environment import Environment
from Babylon.utils.interactive import confirm_deletion
from Babylon.utils.messages import SUCCESS_DELETED
from Babylon.utils.request import oauth_request
from Babylon.utils.response import CommandResponse
from Babylon.utils.typing import QueryType

logger = getLogger("Babylon")
env = Environment()


@command()
@wrapcontext
@pass_context
@timing_decorator
@pass_azure_token("csm_api")
@option("-D", "force_validation", is_flag=True, help="Delete on force mode")
@argument("id", type=QueryType(), required=False)
@inject_context_with_resource({"api": ['url', 'organization_id']})
def delete(ctx: Context, context: Any, azure_token: str, id: str, force_validation: bool = False) -> CommandResponse:
    """
    Delete a solution
    """
    organization_id = context['api_organization_id']
    solution_id = env.configuration.get_var(resource_id=ctx.parent.parent.command.name, var_name="solution_id")
    if not id:
        logger.error(f"You trying to {ctx.command.name} {ctx.parent.command.name} in configuration")
        logger.error(f"Current value: {solution_id}")
    if not solution_id:
        logger.error("Solution id is missing")
        return CommandResponse.fail()
    solution_id = id or solution_id
    if not force_validation and not confirm_deletion("solution", solution_id):
        return CommandResponse.fail()
    response = oauth_request(f"{context['api_url']}/organizations/{organization_id}/solutions/{solution_id}",
                             azure_token,
                             type="DELETE")
    if response is None:
        return CommandResponse.fail()
    logger.info(SUCCESS_DELETED("solution", solution_id))
    return CommandResponse.success()

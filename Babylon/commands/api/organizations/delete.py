from logging import getLogger
from typing import Any
from click import Context, argument, command, pass_context
from click import option
from Babylon.utils.interactive import confirm_deletion
from Babylon.utils.decorators import inject_context_with_resource
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.decorators import wrapcontext
from Babylon.utils.messages import SUCCESS_DELETED
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.environment import Environment
from Babylon.utils.typing import QueryType
from Babylon.utils.request import oauth_request

logger = getLogger("Babylon")
env = Environment()


@command()
@wrapcontext
@pass_context
@timing_decorator
@pass_azure_token("csm_api")
@option("-D", "force_validation", is_flag=True, help="Delete on force mode")
@argument("id", type=QueryType(), required=False)
@inject_context_with_resource({"api": ['url', 'organization_id']}, required=False)
def delete(ctx: Context, context: Any, azure_token: str, id: str, force_validation: bool = False) -> CommandResponse:
    """Delete an organization"""
    if not id:
        logger.error(f"You trying to {ctx.command.name} {ctx.parent.command.name} referenced in configuration")
        logger.error(f"Current value: {context['api_organization_id']}")
    organization_id = id or context['api_organization_id']

    logger.info(f"You trying to delete the '{organization_id}' organization")
    if not force_validation and not confirm_deletion("organization", organization_id):
        return CommandResponse.fail()
    if not organization_id:
        logger.error("Organization id is missing")
        return CommandResponse.fail()
    response = oauth_request(f"{context['api_url']}/organizations/{organization_id}", azure_token, type="DELETE")
    if response is None:
        return CommandResponse.fail()
    logger.info(SUCCESS_DELETED("organization", organization_id))
    return CommandResponse.success()

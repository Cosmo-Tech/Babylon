from logging import getLogger
from typing import Any
from click import Context, command, pass_context
from click import argument
from click import option
from Babylon.utils.interactive import confirm_deletion
from Babylon.utils.decorators import inject_context_with_resource, timing_decorator, wrapcontext
from Babylon.utils.environment import Environment
from Babylon.utils.messages import SUCCESS_DELETED
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.request import oauth_request
from Babylon.utils.typing import QueryType

logger = getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@pass_context
@timing_decorator
@pass_azure_token("csm_api")
@option("-D", "force_validation", is_flag=True, help="Force Delete")
@argument("id", type=QueryType())
@inject_context_with_resource({"api": ['url', 'organization_id']})
def delete(
    ctx: Context,
    context: Any,
    azure_token: str,
    id: str,
    force_validation: bool = False,
) -> CommandResponse:
    """Delete a dataset"""
    if not force_validation and not confirm_deletion("dataset", id):
        return CommandResponse.fail()
    response = oauth_request(f"{context['api_url']}/organizations/{context['api_organization_id']}/datasets/{id}",
                             azure_token,
                             type="DELETE")
    if response is None:
        return CommandResponse.fail()
    logger.info(SUCCESS_DELETED("dataset", id))
    return CommandResponse.success()

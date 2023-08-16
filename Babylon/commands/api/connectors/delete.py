import logging

from typing import Any
from click import argument
from click import command
from click import option
from Babylon.utils.interactive import confirm_deletion
from Babylon.utils.decorators import inject_context_with_resource, timing_decorator, wrapcontext
from Babylon.utils.typing import QueryType
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.environment import Environment
from Babylon.utils.request import oauth_request
from Babylon.utils.messages import SUCCESS_DELETED

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@timing_decorator
@pass_azure_token("csm_api")
@option("-D", "force_validation", is_flag=True, help="Force Delete")
@argument("id", type=QueryType())
@inject_context_with_resource({"api": ["url"]})
def delete(
    context: Any,
    azure_token: str,
    id: str,
    force_validation: bool = False,
) -> CommandResponse:
    """Delete a registered connector"""
    if not force_validation and not confirm_deletion("connector", id):
        return CommandResponse.fail()
    response = oauth_request(f"{context['api_url']}/connectors/{id}", azure_token, type="DELETE")
    if response is None:
        return CommandResponse.fail()
    logger.info(SUCCESS_DELETED("connector", id))
    return CommandResponse.success()

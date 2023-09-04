import polling2
import logging

from typing import Any
from click import Context, command, pass_context
from click import option
from click import argument
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.interactive import confirm_deletion
from Babylon.utils.request import oauth_request
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.typing import QueryType

logger = logging.getLogger("Babylon")


@command()
@wrapcontext
@pass_context
@pass_azure_token("graph")
@option("-D", "force_validation", is_flag=True, help="Delete on force mode")
@argument("object_id", type=QueryType(), required=False)
@inject_context_with_resource({"app": ['id', 'principal_id']}, required=False)
def delete(ctx: Context,
           context: Any,
           azure_token: str,
           object_id: str,
           force_validation: bool = False) -> CommandResponse:
    """
    Delete an app in Active Directory
    https://learn.microsoft.com/en-us/graph/api/application-delete
    """
    if not object_id:
        logger.error(f"You trying to {ctx.command.name} {ctx.parent.command.name} referenced in configuration")
        logger.error(f"Current value: {context['app_id']}")
    object_id = context['app_id']
    if not force_validation and not confirm_deletion("registration", object_id):
        return CommandResponse.fail()
    logger.info(f"Deleting app registration {object_id}")
    route = f"https://graph.microsoft.com/v1.0/applications/{object_id}"
    sp_response = polling2.poll(lambda: oauth_request(route, azure_token, type="DELETE"),
                                check_success=is_correct_response_app,
                                step=1,
                                timeout=60)

    if sp_response is None:
        return CommandResponse.fail()
    sp_response = sp_response.json()
    logger.info("Successfully deleted")
    return CommandResponse.success()


def is_correct_response_app(response):
    if response is None:
        return CommandResponse.fail()

import logging

from azure.core.credentials import AccessToken
from click import command
from click import pass_context
from click import Context
from click import option
from click import argument

from ........utils.interactive import confirm_deletion
from ........utils.request import oauth_request
from ........utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@pass_context
@argument("registration_id")
@option("-f", "--force", "force_validation", is_flag=True, help="Don't ask for validation before delete")
def delete(ctx: Context, registration_id: str, force_validation: bool = False) -> CommandResponse:
    """
    Delete an app in active directory
    https://learn.microsoft.com/en-us/graph/api/application-delete
    """
    if not force_validation and not confirm_deletion("registration", registration_id):
        return CommandResponse.fail()
    access_token = ctx.find_object(AccessToken).token
    logger.info(f"Deleting app registration {registration_id}")
    route = f"https://graph.microsoft.com/v1.0/applications/{registration_id}"
    response = oauth_request(route, access_token, type="DELETE")
    if response is None:
        return CommandResponse.fail()
    logger.info(f"Successfully launched deletion of registration {registration_id}")
    return CommandResponse.success()

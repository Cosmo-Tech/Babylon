import logging

from azure.identity import DefaultAzureCredential
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
@argument("application_id")
@option("-f", "--force", "force_validation", is_flag=True, help="Don't ask for validation before delete")
def delete(ctx: Context, application_id: str, force_validation: bool = False) -> CommandResponse:
    """
    Delete an app in active directory
    https://learn.microsoft.com/en-us/graph/api/application-post-applications?view=graph-rest-1.0
    """
    if not force_validation and not confirm_deletion("registration", application_id):
        return CommandResponse.fail()
    credentials = ctx.find_object(DefaultAzureCredential)
    logger.info(f"Deleting app registration {application_id}")
    access_token = credentials.get_token("https://graph.microsoft.com").token
    route = f"https://graph.microsoft.com/v1.0/applications/{application_id}"
    response = oauth_request(route, access_token, type="DELETE")
    if response is None:
        return CommandResponse.fail()
    logger.info(f"Successfully launched deletion of registration {application_id}")
    return CommandResponse.success()

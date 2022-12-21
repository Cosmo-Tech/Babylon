import logging

from azure.core.credentials import AccessToken
from click import Context
from click import command
from click import pass_context

from ......utils.logging import table_repr
from ......utils.response import CommandResponse
from ......utils.request import oauth_request
from ......utils.decorators import output_to_file

logger = logging.getLogger("Babylon")


@command()
@pass_context
@output_to_file
def get_all(ctx: Context) -> CommandResponse:
    """Get all workspace information for the given account"""
    access_token = ctx.find_object(AccessToken).token
    url_groups = 'https://api.powerbi.com/v1.0/myorg/groups'
    response = oauth_request(url=url_groups, access_token=access_token)
    if response is None:
        return CommandResponse.fail()
    groups = response.get('value')
    logger.info("\n".join(table_repr(groups)))
    return CommandResponse(data=groups)

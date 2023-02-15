import logging

from click import command

from ......utils.logging import table_repr
from ......utils.response import CommandResponse
from ......utils.request import oauth_request
from ......utils.decorators import output_to_file
from ......utils.credentials import get_azure_token

logger = logging.getLogger("Babylon")


@command()
@output_to_file
def get_all() -> CommandResponse:
    """Get all workspace information for the given account"""
    url_groups = 'https://api.powerbi.com/v1.0/myorg/groups'
    response = oauth_request(url=url_groups, access_token=get_azure_token("powerbi"))
    if response is None:
        return CommandResponse.fail()
    groups = response.json().get('value')
    logger.info("\n".join(table_repr(groups)))
    return CommandResponse.success(groups)

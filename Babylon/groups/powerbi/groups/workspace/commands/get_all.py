import logging
import requests

from click import command
from click import pass_context
from click import Context

from ......utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@pass_context
def get_all(ctx: Context) -> CommandResponse:
    """Get all workspace information for the given account"""
    url_groups = 'https://api.powerbi.com/v1.0/myorg/groups'
    access_token = ctx.obj.token
    header = {'Content-Type': 'application/json', 'Authorization': f'Bearer {access_token}'}
    try:
        response = requests.get(url=url_groups, headers=header)
    except Exception as e:
        logger.error(f"Request failed {e}")
        return CommandResponse(status_code=CommandResponse.STATUS_ERROR)
    logger.info(response.json())
    return CommandResponse(data=response.json())

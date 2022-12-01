import logging
import requests

from click import command
from click import option
from click import pass_context
from click import Context

from ......utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@pass_context
@option("-i", "--id", "id")
@option("-n", "--name", "name")
def get(ctx: Context, id: str, name: str) -> CommandResponse:
    """Get a specific workspace information"""
    url_groups = 'https://api.powerbi.com/v1.0/myorg/groups'
    access_token = ctx.obj.token
    header = {'Content-Type': 'application/json', 'Authorization': f'Bearer {access_token}'}
    params = {"$filter": f"id eq'{id}'"} if id else {"$filter": f"name eq '{name}'"}
    try:
        response = requests.get(url=url_groups, headers=header, params=params)
    except Exception as e:
        logger.error(f"Request failed {e}")
        return CommandResponse(status_code=CommandResponse.STATUS_ERROR)
    logger.info(response.json())
    return CommandResponse(data=response.json())

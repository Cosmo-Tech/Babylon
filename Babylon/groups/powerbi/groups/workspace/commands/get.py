import logging
import requests

from click import command
from click import option
from click import pass_context
from click import Context


logger = logging.getLogger("Babylon")


@command()
@pass_context
@option("-i", "--id", "id")
@option("-n", "--name", "name")
def get(ctx: Context, id: str, name: str):
    """Get a specific workspace information"""
    url_groups = 'https://api.powerbi.com/v1.0/myorg/groups'
    access_token = ctx.obj.token
    header = {'Content-Type': 'application/json', 'Authorization': f'Bearer {access_token}'}
    params = {"$filter": f"id eq'{id}'"} if id else {"$filter": f"name eq '{name}'"}
    response = requests.get(url=url_groups, headers=header, params=params)
    logger.info(response.json())

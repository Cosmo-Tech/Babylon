import logging
from click import command
from click import pass_context
from click import Context
import requests

logger = logging.getLogger("Babylon")


@command()
@pass_context
def get_all(ctx: Context):
    """Get all workspace information for the given account"""
    url_groups = 'https://api.powerbi.com/v1.0/myorg/groups'
    access_token = ctx.obj.token
    header = {'Content-Type': 'application/json', 'Authorization': f'Bearer {access_token}'}
    api_out = requests.get(url=url_groups, headers=header)
    logger.info(api_out.json())

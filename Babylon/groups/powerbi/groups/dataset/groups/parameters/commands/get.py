import logging
import requests

from click import command
from click import argument
from click import pass_context
from click import Context

from ........utils.decorators import require_platform_key

logger = logging.getLogger("Babylon")


@command()
@pass_context
@require_platform_key("powerbi_workspace_id")
@argument("report_id")
def get(ctx: Context, powerbi_workspace_id: str, report_id: str):
    """Get datasource details of a given report"""
    access_token = ctx.obj.token
    header = {'Content-Type': 'application/json', 'Authorization': f'Bearer {access_token}'}
    update_url = f"https://api.powerbi.com/v1.0/myorg/groups/{powerbi_workspace_id}/reports/{report_id}/datasources"
    response = requests.get(url=update_url, headers=header)
    logger.info(response.json())
